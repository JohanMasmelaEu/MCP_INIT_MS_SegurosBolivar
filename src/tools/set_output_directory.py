"""Tool: set_output_directory — configura el directorio de salida para proyectos generados."""

import logging

from src.tools.initialize_project import container_path_to_host, normalize_path_for_container
from src.utils.settings import get_all_settings, set_output_directory

logger = logging.getLogger("mcp_init_ms.tools.set_output_directory")


def handle_set_output_directory(path: str) -> dict:
    """Configura el directorio base donde se generan los proyectos.

    Normaliza el path proporcionado (Windows o Unix) al formato del container
    antes de persistirlo. Asi, initialize_project siempre recibe un path valido.

    Args:
        path: Ruta absoluta del directorio de salida (puede ser Windows o Unix).

    Returns:
        Resultado con el path configurado (container y host) y settings actuales.
    """
    try:
        # Normalizar path Windows al formato container antes de persistir
        container_path = normalize_path_for_container(path)
        logger.info("Path recibido '%s' normalizado a '%s'", path, container_path)

        # Persistir el path normalizado (del container)
        normalized = set_output_directory(container_path)

        # Traducir de vuelta al host para mostrar al usuario
        host_path = container_path_to_host(normalized)

        return {
            "status": "success",
            "output_directory": normalized,
            "host_path": host_path,
            "message": (
                f"Directorio de salida configurado.\n"
                f"  - En tu maquina: {host_path}\n"
                f"  - En el container: {normalized}\n"
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
