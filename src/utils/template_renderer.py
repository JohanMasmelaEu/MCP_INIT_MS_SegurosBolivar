"""Motor de renderizado de templates Jinja2.

Carga templates desde el directorio templates/<stack>/ y los renderiza
con la configuracion del proyecto.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

logger = logging.getLogger("mcp_init_ms.utils.template_renderer")

TEMPLATES_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


class TemplateRenderer:
    """Renderiza templates Jinja2 para un stack especifico.

    Attributes:
        stack: Identificador del stack (subdirectorio en templates/).
        env: Entorno Jinja2 configurado.
    """

    def __init__(self, stack: str = "java-spring-boot") -> None:
        """Inicializa el renderer para el stack indicado.

        Args:
            stack: Subdirectorio dentro de templates/ con los .j2 files.
        """
        self.stack = stack
        templates_dir = TEMPLATES_BASE_DIR / stack

        if not templates_dir.exists():
            raise FileNotFoundError(f"Directorio de templates no encontrado: {templates_dir}")

        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Filtros custom
        self.env.filters["to_camel_case"] = _to_camel_case
        self.env.filters["to_pascal_case"] = _to_pascal_case
        self.env.filters["to_snake_case"] = _to_snake_case
        self.env.filters["to_upper_snake"] = _to_upper_snake
        self.env.filters["pluralize_es"] = _pluralize_es
        self.env.filters["java_type_import"] = _java_type_import

    def render(self, template_path: str, context: dict) -> str:
        """Renderiza un template con el contexto dado.

        Args:
            template_path: Ruta relativa al template dentro del directorio del stack.
            context: Variables disponibles en el template.

        Returns:
            Contenido renderizado como string.
        """
        template = self.env.get_template(template_path)
        return template.render(**context)

    def has_template(self, template_path: str) -> bool:
        """Verifica si un template existe.

        Args:
            template_path: Ruta relativa al template.

        Returns:
            True si el template existe.
        """
        try:
            self.env.get_template(template_path)
            return True
        except Exception:
            return False


def _to_camel_case(value: str) -> str:
    """Convierte snake_case o kebab-case a camelCase."""
    parts = value.replace("-", "_").split("_")
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def _to_pascal_case(value: str) -> str:
    """Convierte snake_case o kebab-case a PascalCase."""
    parts = value.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts)


def _to_snake_case(value: str) -> str:
    """Convierte camelCase o PascalCase a snake_case."""
    result = []
    for i, char in enumerate(value):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)


def _to_upper_snake(value: str) -> str:
    """Convierte a UPPER_SNAKE_CASE."""
    return _to_snake_case(value).upper()


def _pluralize_es(value: str) -> str:
    """Pluralizacion basica en espanol (para nombres de tablas/recursos)."""
    if value.endswith("z"):
        return value[:-1] + "ces"
    if value.endswith(("s", "x")):
        return value + "es"
    if value.endswith(("a", "e", "i", "o", "u")):
        return value + "s"
    return value + "es"


def _java_type_import(field_type: str) -> str:
    """Retorna el import Java necesario para un tipo de campo.

    Args:
        field_type: Tipo del campo (String, Long, BigDecimal, etc.)

    Returns:
        Import statement completo o string vacio si no requiere import.
    """
    imports_map = {
        "BigDecimal": "java.math.BigDecimal",
        "LocalDate": "java.time.LocalDate",
        "LocalDateTime": "java.time.LocalDateTime",
        "UUID": "java.util.UUID",
    }
    return imports_map.get(field_type, "")
