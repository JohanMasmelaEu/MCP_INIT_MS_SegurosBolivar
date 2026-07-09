"""Tool: configure_infrastructure — actualiza la configuracion de infraestructura local."""

import json
import logging
from pathlib import Path

from src.generators.java_spring_boot import JavaSpringBootGenerator
from src.models.project_config import ProjectConfig

logger = logging.getLogger("mcp_init_ms.tools.configure_infrastructure")


def handle_configure_infrastructure(project_path: str, infra_dict: dict) -> dict:
    """Actualiza docker-compose, seed-ssm y .env.sample con nueva configuracion.

    Args:
        project_path: Ruta al proyecto existente.
        infra_dict: Configuracion de BD, SSM params y variables.

    Returns:
        Resultado con status y archivos modificados.
    """
    root = Path(project_path)

    if not root.exists():
        return {"status": "error", "message": f"El directorio '{project_path}' no existe."}

    config_file = root / ".kiro" / "project-config.json"
    if not config_file.exists():
        return {
            "status": "error",
            "message": (
                f"No se encontro .kiro/project-config.json en '{project_path}'. "
                "Este archivo se genera con initialize_project."
            ),
        }

    try:
        existing_config_dict = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"status": "error", "message": f"Error leyendo configuracion existente: {e}"}

    # Merge de la nueva configuracion de infra sobre la existente
    if "database" in infra_dict:
        existing_config_dict["database"].update(infra_dict["database"])
    if "observability" in infra_dict:
        existing_config_dict.setdefault("observability", {}).update(infra_dict["observability"])
    if "integrations" in infra_dict:
        existing_config_dict.setdefault("integrations", {}).update(infra_dict["integrations"])

    try:
        config = ProjectConfig(**existing_config_dict)
    except Exception as e:
        return {"status": "error", "message": f"Configuracion resultante invalida: {e}"}

    try:
        generator = JavaSpringBootGenerator(config, root)
        modified_files = generator.regenerate_infrastructure()

        # Persistir configuracion actualizada
        config_file.write_text(
            json.dumps(config.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info("Infraestructura actualizada: %d archivos en %s", len(modified_files), root)

        return {
            "status": "success",
            "files_modified": len(modified_files),
            "files": [str(f) for f in modified_files],
        }
    except Exception as e:
        logger.exception("Error actualizando infraestructura en '%s'", project_path)
        return {"status": "error", "message": f"Error durante la actualizacion: {e}"}
