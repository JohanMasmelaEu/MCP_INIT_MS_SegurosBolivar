"""Modulo de configuracion persistente del MCP.

Almacena preferencias del usuario (como el directorio de salida)
en un archivo JSON que sobrevive entre sesiones gracias al volumen
Docker mcp-init-settings:/settings.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mcp_init_ms.utils.settings")

_SETTINGS_DIR = Path("/settings")
_SETTINGS_FILE = _SETTINGS_DIR / "mcp-settings.json"
_DEFAULT_OUTPUT_DIR = "/repos"


def _get_settings_path() -> Path:
    """Retorna el path del archivo de settings.

    Returns:
        Path al archivo de configuracion persistente.
    """
    return _SETTINGS_FILE


def _load_settings() -> dict:
    """Lee las settings desde disco.

    Returns:
        Diccionario con las settings actuales, o vacio si no existe.
    """
    path = _get_settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Error leyendo settings, usando defaults: %s", e)
        return {}


def _save_settings(settings: dict) -> None:
    """Persiste las settings en disco.

    Args:
        settings: Diccionario completo a persistir.
    """
    path = _get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Settings guardadas en: %s", path)


def get_output_directory() -> str:
    """Obtiene el directorio de salida configurado.

    Returns:
        Path configurado o el default '/repos'.
    """
    settings = _load_settings()
    return settings.get("output_directory", _DEFAULT_OUTPUT_DIR)


def set_output_directory(path: str) -> str:
    """Configura el directorio de salida para proyectos generados.

    Valida que el directorio exista o pueda crearse dentro del volumen montado.

    Args:
        path: Ruta absoluta donde se generaran los proyectos (dentro de /repos).

    Returns:
        Path configurado (normalizado).

    Raises:
        ValueError: Si el path no es valido o no se puede acceder.
    """
    target = Path(path).resolve()

    if not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(
                f"No se puede crear el directorio '{path}': {e}. "
                "Verifica que el path este dentro del volumen montado en /repos."
            ) from e

    if not target.is_dir():
        raise ValueError(f"La ruta '{path}' existe pero no es un directorio.")

    normalized = str(target)
    settings = _load_settings()
    settings["output_directory"] = normalized
    _save_settings(settings)

    return normalized


def get_all_settings() -> dict:
    """Retorna todas las settings actuales.

    Returns:
        Diccionario con todas las configuraciones persistidas.
    """
    settings = _load_settings()
    settings.setdefault("output_directory", _DEFAULT_OUTPUT_DIR)
    return settings
