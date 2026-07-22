"""MCP Server entry point para inicializacion de microservicios - Seguros Bolivar.

Este servidor expone tools que Kiro consume para generar arquetipos
completos de proyectos Java 21 / Spring Boot 4.x / Gradle.
Transport: stdio (ejecucion local via Docker).
"""

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.tools.list_available_stacks import handle_list_available_stacks
from src.tools.get_required_inputs import handle_get_required_inputs
from src.tools.get_project_plan import handle_get_project_plan
from src.tools.initialize_project import handle_initialize_project
from src.tools.add_domain_module import handle_add_domain_module
from src.tools.configure_infrastructure import handle_configure_infrastructure
from src.tools.get_blueprint import handle_get_blueprint
from src.tools.set_output_directory import handle_set_output_directory
from src.tools.stack_guidelines import (
    handle_ingest_stack_guidelines,
    handle_get_stack_guidelines,
    handle_apply_stack_guidelines,
)


def _parse_config(config) -> dict:
    """Parsea el input de configuracion independientemente del formato.

    Acepta:
    - str: JSON string con la config (formato esperado original).
    - str con doble escape: cuando el LLM escapa las comillas una vez de mas.
    - dict: JSON ya parseado (cuando el LLM lo pasa como objeto directamente).

    Ademas, si el dict viene agrupado por categorias del schema de get_required_inputs
    (project_identity, domain_modules, database, etc.), lo aplana al formato
    esperado por ProjectConfig.

    Args:
        config: Configuracion como string JSON o dict.

    Returns:
        Diccionario plano compatible con ProjectConfig.
    """
    if isinstance(config, dict):
        config_dict = config
    elif isinstance(config, str):
        config_dict = _parse_json_string(config)
    else:
        raise ValueError(f"config debe ser str o dict, recibido: {type(config).__name__}")

    return _flatten_categorized_config(config_dict)


def _parse_json_string(raw: str) -> dict:
    """Parsea un JSON string manejando doble-escape y formatos irregulares.

    El LLM a veces envia el JSON con escaped quotes:
    - Normal: {"project_name": "test"}
    - Escaped: {\"project_name\": \"test\"}  (backslash + quote como chars literales)

    Args:
        raw: String JSON potencialmente con escape extra.

    Returns:
        Diccionario parseado.
    """
    # Intentar parseo directo primero
    try:
        result = json.loads(raw)
        # Si el resultado es un string, puede ser doble-encoded (string dentro de string)
        if isinstance(result, str):
            return json.loads(result)
        return result
    except (json.JSONDecodeError, TypeError):
        pass

    # Si falla, el string probablemente tiene backslash-quote literales (\")
    # Reemplazar la secuencia de 2 chars: backslash seguido de quote
    unescaped = raw.replace('\\\"', '"').replace("\\'", "'")

    # Si despues de unescape empieza y termina con comilla, quitarlas
    stripped = unescaped.strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        stripped = stripped[1:-1]
        # Despues de quitar comillas externas, puede necesitar otro unescape
        stripped = stripped.replace('\\\\', '\\').replace('\\"', '"')

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Intentar con el unescaped sin quitar comillas
    try:
        return json.loads(unescaped)
    except json.JSONDecodeError:
        pass

    raise ValueError(
        f"No se pudo parsear config como JSON. Primeros 100 chars: {repr(raw[:100])}"
    )


def _flatten_categorized_config(config_dict: dict) -> dict:
    """Aplana un config agrupado por categorias al formato plano de ProjectConfig.

    Si el dict ya esta en formato plano (tiene 'project_name' en raiz), lo retorna tal cual.
    Si viene agrupado por categorias (project_identity, domain_modules, etc.), lo aplana.

    Args:
        config_dict: Diccionario potencialmente agrupado.

    Returns:
        Diccionario plano listo para ProjectConfig(**flat).
    """
    # Si ya tiene project_name en raiz, esta en formato plano
    if "project_name" in config_dict:
        return config_dict

    flat = {}

    # project_identity → campos planos en raiz
    if "project_identity" in config_dict:
        flat.update(config_dict["project_identity"])

    # domain_modules → extraer campo modules
    if "domain_modules" in config_dict:
        dm = config_dict["domain_modules"]
        if isinstance(dm, dict) and "modules" in dm:
            flat["modules"] = dm["modules"]
        elif isinstance(dm, list):
            flat["modules"] = dm

    # database → objeto anidado
    if "database" in config_dict:
        flat["database"] = config_dict["database"]

    # authentication → extraer auth_strategy
    if "authentication" in config_dict:
        auth = config_dict["authentication"]
        if isinstance(auth, dict) and "auth_strategy" in auth:
            flat["auth_strategy"] = auth["auth_strategy"]
        elif isinstance(auth, str):
            flat["auth_strategy"] = auth

    # integrations → objeto anidado
    if "integrations" in config_dict:
        flat["integrations"] = config_dict["integrations"]

    # observability → objeto anidado
    if "observability" in config_dict:
        flat["observability"] = config_dict["observability"]

    # artifactory → extraer artifactory_url
    if "artifactory" in config_dict:
        art = config_dict["artifactory"]
        if isinstance(art, dict) and "artifactory_url" in art:
            flat["artifactory_url"] = art["artifactory_url"]
        elif isinstance(art, str):
            flat["artifactory_url"] = art

    # mcp_marketplace → selected_mcps
    if "mcp_marketplace" in config_dict:
        mkt = config_dict["mcp_marketplace"]
        if isinstance(mkt, dict) and "selected_mcps" in mkt:
            flat["selected_mcps"] = mkt["selected_mcps"]
        elif isinstance(mkt, list):
            flat["selected_mcps"] = mkt

    # project_metadata → campos planos
    if "project_metadata" in config_dict:
        flat.update(config_dict["project_metadata"])

    # ports → campos planos (app_port, localstack_port, redis_port)
    if "ports" in config_dict:
        flat.update(config_dict["ports"])

    # localstack → extraer localstack_services
    if "localstack" in config_dict:
        ls = config_dict["localstack"]
        if isinstance(ls, dict) and "localstack_services" in ls:
            flat["localstack_services"] = ls["localstack_services"]
        elif isinstance(ls, list):
            flat["localstack_services"] = ls

    # security_details → campos planos (cors_allow_credentials, extra_public_paths, openapi_base_path)
    if "security_details" in config_dict:
        flat.update(config_dict["security_details"])

    # Si quedo vacio despues del flatten, el input no era categorizado ni plano
    if not flat:
        return config_dict

    return flat

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
async def get_project_plan(config: dict) -> str:
    """Genera el plan detallado de archivos y carpetas a crear, SIN ejecutar la generacion.

    Kiro debe mostrar este plan al usuario y obtener confirmacion antes de
    llamar a initialize_project. El plan incluye arbol de archivos, decisiones
    tomadas y pasos siguientes.

    Args:
        config: JSON object con la configuracion completa del proyecto
                (todas las respuestas del usuario segun el schema de get_required_inputs).
    """
    config_dict = _parse_config(config)
    result = handle_get_project_plan(config_dict)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def initialize_project(config: dict, target_path: str = "") -> str:
    """Genera el proyecto completo en disco. SOLO llamar despues de confirmacion del usuario.

    Renderiza todos los templates Jinja2 con los datos del usuario y escribe
    los archivos en el path indicado. El proyecto generado esta listo para
    hacer docker compose up y tener un MS funcional en local.

    Si target_path esta vacio, usa el directorio configurado con set_output_directory.
    Si no se ha configurado ningun directorio, usa /repos como fallback.

    Args:
        config: JSON object con la configuracion completa del proyecto.
        target_path: Ruta base donde se genera el proyecto. Dejar vacio para usar el configurado.
    """
    config_dict = _parse_config(config)
    result = handle_initialize_project(config_dict, target_path or None)
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


@mcp.tool()
async def set_output_directory(path: str) -> str:
    """Configura el directorio base donde se generan los proyectos.

    Una vez configurado, todas las llamadas a initialize_project usaran
    este directorio como default sin necesidad de pasar target_path.
    La configuracion se persiste entre sesiones.

    Ejemplo de uso: el usuario dice "genera mis proyectos en C:/REPOS/SegurosBolivar"
    y a partir de ahi todos los proyectos se crean en esa carpeta.

    Args:
        path: Ruta absoluta del directorio de salida (ej: "/repos", "C:/REPOS/MiEquipo").
    """
    result = handle_set_output_directory(path)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def ingest_stack_guidelines(stack_id: str, raw_content: str, source_filename: str = "") -> str:
    """Persiste el contenido de un documento de lineamientos para un stack tecnologico.

    Flujo completo:
    1. El usuario adjunta un PDF/documento con lineamientos en el chat de Kiro.
    2. Kiro (LLM) extrae el texto del documento adjunto.
    3. Kiro invoca este tool para persistir el contenido crudo.
    4. Kiro analiza el contenido con su LLM y genera un resumen estructurado.
    5. Kiro muestra al usuario: "Asi entendi los lineamientos: ..."
    6. El usuario refina hasta aprobar.
    7. Kiro invoca apply_stack_guidelines con el resultado aprobado.

    Args:
        stack_id: Identificador del stack (ej: "java-spring-boot", "python-fastapi").
        raw_content: Texto completo extraido del documento PDF/Word.
        source_filename: Nombre original del archivo fuente (ej: "Lineamientos_Java_2024.pdf").
    """
    result = handle_ingest_stack_guidelines(stack_id, raw_content, source_filename)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_stack_guidelines(stack_id: str, version: str = "latest") -> str:
    """Obtiene los lineamientos almacenados para un stack tecnologico.

    Usa este tool para recuperar el contenido de lineamientos previamente
    ingresados y analizarlos con tu LLM para generar estandares estructurados.

    Args:
        stack_id: Identificador del stack (ej: "java-spring-boot").
        version: "latest" o "raw" para el contenido crudo, "applied" para los ya aprobados.
    """
    result = handle_get_stack_guidelines(stack_id, version)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def apply_stack_guidelines(stack_id: str, refined_guidelines: str, update_blueprint: bool = True, replace_existing: bool = False) -> str:
    """Persiste los lineamientos refinados como documentacion oficial del stack.

    Invocar SOLO despues de que el usuario haya aprobado el analisis generado
    por Kiro. Los lineamientos aprobados se convierten en la referencia oficial
    del stack y se muestran en el Archetype Visualizer (tab Estandares).

    Opcionalmente actualiza el blueprint tecnico del stack en blueprints/.

    Args:
        refined_guidelines: JSON string con los estandares aprobados. Formato:
            {"stack_name": "...", "categories": [{"name": "...", "rules": [{"rule": "...", "convention": "...", "example": "..."}]}]}
        stack_id: Identificador del stack.
        update_blueprint: Si True, genera/actualiza el blueprint .md del stack.
        replace_existing: Si True, reemplaza guidelines existentes. Si False, mergea con los anteriores.
    """
    guidelines_dict = json.loads(refined_guidelines) if isinstance(refined_guidelines, str) else refined_guidelines
    result = handle_apply_stack_guidelines(stack_id, guidelines_dict, update_blueprint, replace_existing)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    logger.info("Iniciando MCP_INIT_MS_SegurosBolivar v1.0.0 (stdio)")
    # Arrancar visualizador de arquetipo en background (puerto 9752)
    from src.engine.visualizer import start_visualizer
    start_visualizer()
    mcp.run(transport="stdio")
