"""Tool: set_output_directory — configura el directorio de salida para proyectos generados."""

import logging

from src.utils.settings import get_all_settings, set_output_directory

logger = logging.getLogger("mcp_init_ms.tools.set_output_directory")


def handle_set_output_directory(path: str) -> dict:
    """Configura el directorio base donde se generan los proyectos.

    Una vez configurado, todas las llamadas a initialize_project usaran
    este directorio como default (sin necesidad de pasar target_path).

    Args:
        path: Ruta absoluta del directorio de salida.

    Returns:
        Resultado con el path configurado y las settings actuales.
    """
    try:
        normalized = set_output_directory(path)
        logger.info("Output directory configurado: %s", normalized)

        return {
            "status": "success",
            "output_directory": normalized,
            "message": (
                f"Directorio de salida configurado: {normalized}. "
                "Todos los proyectos generados con initialize_project se crearan aqui "
                "a menos que se indique un target_path diferente."
            ),
            "current_settings": get_all_settings(),
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.exception("Error configurando output directory")
        return {"status": "error", "message": f"Error inesperado: {e}"}
