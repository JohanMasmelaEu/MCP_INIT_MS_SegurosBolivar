"""Tool: initialize_project — genera el proyecto completo en disco."""

import logging
from pathlib import Path
from typing import Optional

from src.generators.java_spring_boot import JavaSpringBootGenerator
from src.models.project_config import ProjectConfig
from src.utils.settings import get_output_directory

logger = logging.getLogger("mcp_init_ms.tools.initialize_project")


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
        target_path = get_output_directory()
        logger.info("Usando output directory configurado: %s", target_path)

    try:
        config = ProjectConfig(**config_dict)
    except Exception as e:
        return {"status": "error", "message": f"Configuracion invalida: {e}"}

    project_root = Path(target_path) / config.project_name

    if project_root.exists() and any(project_root.iterdir()):
        return {
            "status": "error",
            "message": (
                f"El directorio '{project_root}' ya existe y no esta vacio. "
                "Elimine su contenido o elija otro nombre de proyecto."
            ),
        }

    try:
        generator = JavaSpringBootGenerator(config, project_root)
        created_files = generator.generate()

        logger.info("Proyecto '%s' generado: %d archivos en %s", config.project_name, len(created_files), project_root)

        # Actualizar estado del visualizador
        try:
            from src.engine.visualizer import update_project_state, _build_tree
            update_project_state({
                "status": "ok",
                "project_name": config.project_name,
                "config": config.model_dump(mode="json"),
                "tree": _build_tree(project_root, max_depth=4),
            })
        except Exception:
            pass  # Visualizer es opcional, no bloquea la generacion

        return {
            "status": "success",
            "project_name": config.project_name,
            "path": str(project_root),
            "files_created": len(created_files),
            "next_steps": [
                f"1. cd {config.project_name}",
                "2. Copiar development/.env.sample a .env y configurar ARTIFACTORY_USER / ARTIFACTORY_PASSWORD",
                f"3. cd development/docker-local-ms && docker compose --env-file ../../.env up -d",
                f"4. Swagger UI: http://localhost:8080{config.context_path}/swagger-ui.html",
                f"5. Health check: http://localhost:8080{config.context_path}/actuator/health",
            ],
        }
    except Exception as e:
        logger.exception("Error generando proyecto '%s'", config.project_name)
        return {"status": "error", "message": f"Error durante la generacion: {e}"}
