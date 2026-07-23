"""Tool: add_domain_module — agrega un modulo de dominio a un proyecto existente."""

import json
import logging
from pathlib import Path

from src.generators.java_spring_boot import JavaSpringBootGenerator
from src.generators.node_express import NodeExpressGenerator
from src.generators.python_fastapi import PythonFastApiGenerator
from src.models.project_config import DomainModule, ProjectConfig

# Mapeo de stack_id a clase generadora
_GENERATORS = {
    "java-spring-boot": JavaSpringBootGenerator,
    "node-express": NodeExpressGenerator,
    "python-fastapi": PythonFastApiGenerator,
}

logger = logging.getLogger("mcp_init_ms.tools.add_domain_module")


def handle_add_domain_module(project_path: str, module_dict: dict) -> dict:
    """Agrega un modulo de dominio completo a un proyecto existente.

    Lee la configuracion existente del proyecto y genera solo los archivos
    del nuevo modulo (controller, DTOs, service, repository, entity, tests).

    Args:
        project_path: Ruta al proyecto existente.
        module_dict: Configuracion del modulo a agregar.

    Returns:
        Resultado con status y archivos creados.
    """
    root = Path(project_path)

    if not root.exists():
        return {"status": "error", "message": f"El directorio '{project_path}' no existe."}

    # Intentar leer configuracion del proyecto existente
    config_file = root / ".kiro" / "project-config.json"
    if not config_file.exists():
        return {
            "status": "error",
            "message": (
                f"No se encontro .kiro/project-config.json en '{project_path}'. "
                "Este archivo se genera con initialize_project y contiene la configuracion del proyecto."
            ),
        }

    try:
        existing_config_dict = json.loads(config_file.read_text(encoding="utf-8"))
        config = ProjectConfig(**existing_config_dict)
    except Exception as e:
        return {"status": "error", "message": f"Error leyendo configuracion existente: {e}"}

    try:
        new_module = DomainModule(**module_dict)
    except Exception as e:
        return {"status": "error", "message": f"Configuracion del modulo invalida: {e}"}

    # Verificar que el modulo no existe ya
    existing_names = [m.module_name for m in config.modules]
    if new_module.module_name in existing_names:
        return {
            "status": "error",
            "message": f"El modulo '{new_module.module_name}' ya existe en el proyecto.",
        }

    try:
        stack = config.stack
        generator_class = _GENERATORS.get(stack)
        if not generator_class:
            return {
                "status": "error",
                "message": f"Stack '{stack}' no soportado. Stacks disponibles: {', '.join(_GENERATORS.keys())}",
            }
        generator = generator_class(config, root)
        created_files = generator.generate_domain_module(new_module)

        # Actualizar project-config.json con el nuevo modulo
        config.modules.append(new_module)
        config_file.write_text(
            json.dumps(config.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info("Modulo '%s' agregado: %d archivos", new_module.module_name, len(created_files))

        return {
            "status": "success",
            "module_name": new_module.module_name,
            "entity_name": new_module.entity_name,
            "files_created": len(created_files),
            "files": [str(f) for f in created_files],
        }
    except Exception as e:
        logger.exception("Error agregando modulo '%s'", new_module.module_name)
        return {"status": "error", "message": f"Error durante la generacion del modulo: {e}"}
