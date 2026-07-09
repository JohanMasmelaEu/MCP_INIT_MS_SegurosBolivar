"""MCP Server entry point para inicializacion de microservicios - Seguros Bolivar.

Este servidor expone tools que Kiro consume para generar arquetipos
completos de proyectos Java 21 / Spring Boot 4.x / Gradle.
Transport: stdio (ejecucion local via Docker).
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from src.tools.list_available_stacks import handle_list_available_stacks
from src.tools.get_required_inputs import handle_get_required_inputs
from src.tools.get_project_plan import handle_get_project_plan
from src.tools.initialize_project import handle_initialize_project
from src.tools.add_domain_module import handle_add_domain_module
from src.tools.configure_infrastructure import handle_configure_infrastructure
from src.tools.get_blueprint import handle_get_blueprint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp_init_ms")

mcp = FastMCP(
    name="MCP_INIT_MS_SegurosBolivar",
    version="1.0.0",
    description=(
        "MCP Server para inicializacion automatizada de microservicios "
        "Java 21 / Spring Boot 4.x en Seguros Bolivar. "
        "Genera arquetipos completos listos para desarrollo local con Docker Compose."
    ),
)


@mcp.tool()
async def list_available_stacks() -> str:
    """Lista los stacks tecnologicos disponibles para generacion de proyectos.

    Retorna un JSON con los stacks soportados, su estado y descripcion.
    V1 soporta unicamente java-spring-boot.
    """
    result = handle_list_available_stacks()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_required_inputs(stack: str) -> str:
    """Devuelve el schema de datos requeridos para generar un proyecto del stack indicado.

    El schema incluye categorias de preguntas (identidad, modulos de dominio,
    base de datos, autenticacion, integraciones, observabilidad, artifactory)
    con tipos, defaults y ejemplos.

    Args:
        stack: Identificador del stack (ej: "java-spring-boot").
    """
    result = handle_get_required_inputs(stack)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_project_plan(config: str) -> str:
    """Genera el plan detallado de archivos y carpetas a crear, SIN ejecutar la generacion.

    Kiro debe mostrar este plan al usuario y obtener confirmacion antes de
    llamar a initialize_project. El plan incluye arbol de archivos, decisiones
    tomadas y pasos siguientes.

    Args:
        config: JSON string con la configuracion completa del proyecto
                (todas las respuestas del usuario segun el schema de get_required_inputs).
    """
    config_dict = json.loads(config)
    result = handle_get_project_plan(config_dict)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def initialize_project(config: str, target_path: str = "/workspace") -> str:
    """Genera el proyecto completo en disco. SOLO llamar despues de confirmacion del usuario.

    Renderiza todos los templates Jinja2 con los datos del usuario y escribe
    los archivos en el path indicado. El proyecto generado esta listo para
    hacer docker compose up y tener un MS funcional en local.

    Args:
        config: JSON string con la configuracion completa del proyecto.
        target_path: Ruta base donde se genera el proyecto (default: /workspace).
    """
    config_dict = json.loads(config)
    result = handle_initialize_project(config_dict, target_path)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def add_domain_module(project_path: str, module_config: str) -> str:
    """Agrega un modulo de dominio completo a un proyecto existente.

    Genera controller, DTOs, service (interface + impl), repository,
    specification, entity y tests para el nuevo modulo.

    Args:
        project_path: Ruta al proyecto existente.
        module_config: JSON string con la configuracion del modulo
                       (module_name, entity_name, table_name, fields).
    """
    module_dict = json.loads(module_config)
    result = handle_add_domain_module(project_path, module_dict)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def configure_infrastructure(project_path: str, infra_config: str) -> str:
    """Actualiza la configuracion de infraestructura local de un proyecto existente.

    Modifica docker-compose.yml, seed-localstack-ssm.sh, .env.sample y
    variables de entorno segun la nueva configuracion proporcionada.

    Args:
        project_path: Ruta al proyecto existente.
        infra_config: JSON string con configuracion de BD, SSM params, variables.
    """
    infra_dict = json.loads(infra_config)
    result = handle_configure_infrastructure(project_path, infra_dict)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_blueprint(stack: str) -> str:
    """Devuelve el blueprint tecnico del stack como texto para usar como contexto.

    El blueprint contiene la documentacion completa del stack tecnologico,
    patrones de implementacion, convenciones y decisiones arquitectonicas.

    Args:
        stack: Identificador del stack (ej: "java-spring-boot").
    """
    result = handle_get_blueprint(stack)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    logger.info("Iniciando MCP_INIT_MS_SegurosBolivar v1.0.0 (stdio)")
    mcp.run(transport="stdio")
