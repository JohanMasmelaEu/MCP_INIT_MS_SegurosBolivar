"""Tool: get_blueprint — devuelve el blueprint tecnico como contexto."""

import logging
from pathlib import Path

logger = logging.getLogger("mcp_init_ms.tools.get_blueprint")

BLUEPRINTS_DIR = Path(__file__).resolve().parent.parent.parent / "blueprints"

# Mapeo de stack id → archivo de blueprint
_BLUEPRINT_FILES = {
    "java-spring-boot": "TECH_STACK_BLUEPRINT.md",
    "python-fastapi": "TECH_STACK_BLUEPRINT_PYTHON.md",
    "node-express": "TECH_STACK_BLUEPRINT_NODE.md",
}


def handle_get_blueprint(stack: str) -> dict:
    """Lee y retorna el blueprint tecnico del stack indicado.

    Args:
        stack: Identificador del stack tecnologico.

    Returns:
        Diccionario con el contenido del blueprint o un error.
    """
    blueprint_filename = _BLUEPRINT_FILES.get(stack)

    if not blueprint_filename:
        available = ", ".join(_BLUEPRINT_FILES.keys())
        return {
            "error": f"Stack '{stack}' no soportado. Stacks con blueprint disponible: {available}",
        }

    blueprint_file = BLUEPRINTS_DIR / blueprint_filename

    if not blueprint_file.exists():
        logger.error("Blueprint no encontrado en: %s", blueprint_file)
        return {
            "error": f"Blueprint file not found for '{stack}'. Expected: {blueprint_filename}",
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
        logger.exception("Error leyendo blueprint para '%s'", stack)
        return {"error": f"Error leyendo blueprint: {e}"}
