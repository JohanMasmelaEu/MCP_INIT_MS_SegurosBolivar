"""Tool: get_blueprint — devuelve el blueprint tecnico como contexto."""

import logging
from pathlib import Path

logger = logging.getLogger("mcp_init_ms.tools.get_blueprint")

BLUEPRINTS_DIR = Path(__file__).resolve().parent.parent.parent / "blueprints"


def handle_get_blueprint(stack: str) -> dict:
    """Lee y retorna el blueprint tecnico del stack indicado.

    Args:
        stack: Identificador del stack tecnologico.

    Returns:
        Diccionario con el contenido del blueprint o un error.
    """
    if stack != "java-spring-boot":
        return {
            "error": f"Stack '{stack}' no soportado. Stacks disponibles: java-spring-boot",
        }

    blueprint_file = BLUEPRINTS_DIR / "TECH_STACK_BLUEPRINT.md"

    if not blueprint_file.exists():
        logger.error("Blueprint no encontrado en: %s", blueprint_file)
        return {
            "error": "Blueprint file not found. The MCP image may be corrupted.",
            "expected_path": str(blueprint_file),
        }

    try:
        content = blueprint_file.read_text(encoding="utf-8")
        return {
            "stack": stack,
            "blueprint": content,
            "note": (
                "Este blueprint documenta el stack tecnologico completo, "
                "patrones de implementacion, convenciones y decisiones arquitectonicas. "
                "Usalo como referencia para generar codigo alineado al estandar."
            ),
        }
    except Exception as e:
        logger.exception("Error leyendo blueprint")
        return {"error": f"Error leyendo blueprint: {e}"}
