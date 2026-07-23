"""Tool: initialize_project — genera el proyecto completo en disco."""

import logging
import os
import re
import shutil
from pathlib import Path
from typing import Optional

from src.generators.java_spring_boot import JavaSpringBootGenerator
from src.generators.node_express import NodeExpressGenerator
from src.generators.python_fastapi import PythonFastApiGenerator
from src.models.project_config import ProjectConfig
from src.utils.settings import get_output_directory

# Mapeo de stack_id a clase generadora
_GENERATORS = {
    "java-spring-boot": JavaSpringBootGenerator,
    "node-express": NodeExpressGenerator,
    "python-fastapi": PythonFastApiGenerator,
}

logger = logging.getLogger("mcp_init_ms.tools.initialize_project")

# Configuracion de volumenes Docker.
# El host monta un directorio local en /repos dentro del container.
# MCP_HOST_VOLUME_PATH: path del host (ej: "C:/REPOS") — leido de env var o default.
# El container siempre ve /repos como mount point.
_CONTAINER_MOUNT = os.environ.get("MCP_CONTAINER_MOUNT", "/repos")
_HOST_VOLUME_PATH = os.environ.get("MCP_HOST_VOLUME_PATH", "C:/REPOS")


def handle_initialize_project(config_dict: dict, target_path: Optional[str] = None) -> dict:
    """Genera todos los archivos del proyecto en el path indicado.

    Si target_path no se proporciona, usa el directorio configurado
    con set_output_directory (o /repos como ultimo fallback).

    Args:
        config_dict: Configuracion completa del proyecto.
        target_path: Ruta base donde se genera. Si es None, usa el configurado.

    Returns:
        Resultado con status, archivos creados y next steps.
    """
    if not target_path:
        raw_path = get_output_directory()
        target_path = normalize_path_for_container(raw_path)
        logger.info("Usando output directory configurado: %s -> %s", raw_path, target_path)
    else:
        target_path = normalize_path_for_container(target_path)
        logger.info("Target path normalizado: %s", target_path)

    # Validar configuracion del proyecto
    try:
        config = ProjectConfig(**config_dict)
    except Exception as e:
        return {"status": "error", "message": f"Configuracion invalida: {e}"}

    project_root = Path(target_path) / config.project_name

    # Fix #1: Verificar que el directorio padre existe y es escribible
    parent_dir = Path(target_path)
    if not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Directorio padre creado: %s", parent_dir)
        except OSError as e:
            return {
                "status": "error",
                "message": (
                    f"No se puede crear el directorio destino '{target_path}': {e}. "
                    "Verifica que el path este dentro del volumen montado."
                ),
            }

    # Fix #2: Verificar accesibilidad (escribible)
    if not os.access(str(parent_dir), os.W_OK):
        return {
            "status": "error",
            "message": (
                f"El directorio '{target_path}' no tiene permisos de escritura. "
                "Verifica los permisos del volumen Docker montado."
            ),
        }

    # Verificar que el proyecto no exista ya
    if project_root.exists() and any(project_root.iterdir()):
        return {
            "status": "error",
            "message": (
                f"El directorio '{project_root}' ya existe y no esta vacio. "
                "Elimine su contenido o elija otro nombre de proyecto."
            ),
        }

    try:
        stack = config.stack
        generator_class = _GENERATORS.get(stack)
        if not generator_class:
            return {
                "status": "error",
                "message": f"Stack '{stack}' no soportado. Stacks disponibles: {', '.join(_GENERATORS.keys())}",
            }
        generator = generator_class(config, project_root)
        created_files = generator.generate()

        logger.info(
            "Proyecto '%s' generado: %d archivos en %s",
            config.project_name,
            len(created_files),
            project_root,
        )

        # Actualizar estado del visualizador (opcional)
        try:
            from src.engine.visualizer import update_project_state, _build_tree

            update_project_state({
                "status": "ok",
                "project_name": config.project_name,
                "config": config.model_dump(mode="json"),
                "tree": _build_tree(project_root, max_depth=4),
            })
        except Exception:
            pass

        # Fix #5: Traducir el path del container de vuelta al host para la respuesta
        host_path = container_path_to_host(str(project_root))

        return {
            "status": "success",
            "project_name": config.project_name,
            "path": host_path,
            "container_path": str(project_root),
            "files_created": len(created_files),
            "next_steps": [
                f"1. cd {host_path}",
                "2. Copiar development/.env.sample a .env y configurar ARTIFACTORY_USER / ARTIFACTORY_PASSWORD",
                f"3. cd development/docker-local-ms && docker compose --env-file ../../.env up -d",
                f"4. Swagger UI: http://localhost:8080{config.context_path}/swagger-ui.html",
                f"5. Health check: http://localhost:8080{config.context_path}/actuator/health",
            ],
        }
    except Exception as e:
        # Fix #6: Rollback — limpiar directorio parcial si la generacion fallo
        logger.exception("Error generando proyecto '%s'", config.project_name)
        if project_root.exists():
            try:
                shutil.rmtree(project_root)
                logger.info("Rollback: directorio parcial '%s' eliminado.", project_root)
            except OSError as cleanup_err:
                logger.warning("No se pudo limpiar directorio parcial: %s", cleanup_err)
        return {"status": "error", "message": f"Error durante la generacion: {e}"}


def normalize_path_for_container(path: str) -> str:
    """Convierte un path de Windows al path equivalente dentro del container Docker.

    El MCP corre en Docker con un volumen montado (ej: -v C:/REPOS:/repos).
    Cuando Kiro pasa un target_path de Windows (ej: C:\\REPOS\\SegurosBolivar\\CUC),
    debe convertirse al path del container (ej: /repos/SegurosBolivar/CUC).

    La configuracion del volumen se lee de variables de entorno:
    - MCP_HOST_VOLUME_PATH: path del host (default: C:/REPOS)
    - MCP_CONTAINER_MOUNT: mount point en container (default: /repos)

    Args:
        path: Ruta proporcionada por el usuario (puede ser Windows o Unix).

    Returns:
        Ruta normalizada para uso dentro del container.
    """
    if not path:
        return _CONTAINER_MOUNT

    # Si ya es un path Unix que empieza con el mount point, retornar tal cual
    if path.startswith(_CONTAINER_MOUNT):
        return path

    # Si es un path Unix generico, retornar tal cual
    if path.startswith("/") and not _is_windows_path(path):
        return path

    # Normalizar separadores a forward slash
    normalized = path.replace("\\", "/")

    # Fix #3: Usar el prefijo del host desde env var (no hardcodeado)
    # Normalizar el host prefix tambien para comparacion
    host_prefix = _HOST_VOLUME_PATH.replace("\\", "/").rstrip("/")

    # Intentar mapear: si el path empieza con el host prefix, reemplazar
    if normalized.lower().startswith(host_prefix.lower()):
        remainder = normalized[len(host_prefix):]
        # Quitar leading slash si quedo
        remainder = remainder.lstrip("/")
        container_path = f"{_CONTAINER_MOUNT}/{remainder}" if remainder else _CONTAINER_MOUNT
        container_path = container_path.replace("//", "/").rstrip("/")
        logger.info("Path '%s' mapeado a container: '%s'", path, container_path)
        return container_path

    # Fallback: intentar regex generico para cualquier drive letter + REPOS
    pattern = re.compile(r"^[a-zA-Z]:/REPOS/?(.*)", re.IGNORECASE)
    match = pattern.match(normalized)
    if match:
        remainder = match.group(1)
        container_path = f"{_CONTAINER_MOUNT}/{remainder}" if remainder else _CONTAINER_MOUNT
        container_path = container_path.replace("//", "/").rstrip("/")
        logger.info("Path '%s' mapeado via regex fallback: '%s'", path, container_path)
        return container_path

    # Si no matchea nada, usar el path tal cual (puede ser un path relativo dentro del container)
    logger.warning(
        "Path '%s' no se pudo mapear al volumen del container. "
        "Intentando usar como path directo dentro del container.",
        path,
    )
    return normalized


def container_path_to_host(container_path: str) -> str:
    """Traduce un path del container de vuelta al path del host Windows.

    Usado para la respuesta al usuario, que necesita saber donde quedo
    el proyecto en su filesystem.

    Args:
        container_path: Path dentro del container (ej: /repos/SegurosBolivar/CUC/mi-ms).

    Returns:
        Path traducido al host (ej: C:/REPOS/SegurosBolivar/CUC/mi-ms).
    """
    if not container_path.startswith(_CONTAINER_MOUNT):
        return container_path

    remainder = container_path[len(_CONTAINER_MOUNT):]
    host_prefix = _HOST_VOLUME_PATH.replace("\\", "/").rstrip("/")
    host_path = f"{host_prefix}{remainder}"
    return host_path


def _is_windows_path(path: str) -> bool:
    """Detecta si un path tiene formato Windows (letra de unidad).

    Args:
        path: Path a evaluar.

    Returns:
        True si parece un path Windows.
    """
    return bool(re.match(r"^[a-zA-Z]:[/\\]", path))
