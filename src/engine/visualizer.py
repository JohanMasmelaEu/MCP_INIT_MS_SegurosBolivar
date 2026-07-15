"""Archetype Visualizer: servidor HTTP en background con UI interactiva.

Se levanta como thread daemon al arrancar el MCP.
Sirve en localhost:9752 una UI web para explorar:
- Arbol de directorios del arquetipo generado
- Estandares del stack tecnologico
- Configuracion y decisiones del proyecto
- Panel de administracion para agregar nuevos stacks

Tambien expone /admin para el formulario de creacion de stacks.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Optional

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from src.utils.settings import get_output_directory

logger = logging.getLogger("mcp_init_ms.engine.visualizer")

VISUALIZER_PORT = 9752
VISUALIZER_HOST = "0.0.0.0"
UI_PATH = Path(__file__).parent / "visualizer_ui.html"
ADMIN_UI_PATH = Path(__file__).parent / "admin_ui.html"
BLUEPRINTS_DIR = Path(__file__).parent.parent.parent / "blueprints"
RULES_DIR = Path(__file__).parent.parent.parent / "rules"
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# In-memory state: ultimo proyecto generado (se actualiza desde el generator)
_last_project_state: Optional[dict] = None


def update_project_state(state: dict) -> None:
    """Actualiza el estado del ultimo proyecto generado para la UI.

    Args:
        state: Diccionario con config, archivos creados y decisiones.
    """
    global _last_project_state
    _last_project_state = state
    logger.info("Visualizer state actualizado: %s", state.get("project_name", "unknown"))


def _get_project_state() -> dict:
    """Lee el estado del proyecto desde memoria o disco.

    Returns:
        Estado del proyecto con config, tree y standards.
    """
    if _last_project_state:
        return _last_project_state

    # Intentar leer del ultimo proyecto generado
    output_dir = get_output_directory()
    output_path = Path(output_dir)

    if not output_path.exists():
        return {"status": "no_project", "message": "No se ha generado ningun proyecto aun."}

    # Buscar project-config.json en subdirectorios
    for config_file in output_path.rglob(".kiro/project-config.json"):
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
            project_root = config_file.parent.parent
            tree = _build_tree(project_root, max_depth=4)
            return {
                "status": "ok",
                "project_name": config.get("project_name", "unknown"),
                "config": config,
                "tree": tree,
            }
        except (json.JSONDecodeError, OSError):
            continue

    return {"status": "no_project", "message": "No se encontro ningun proyecto con .kiro/project-config.json."}


def _build_tree(root: Path, max_depth: int = 4, current_depth: int = 0) -> list:
    """Construye arbol de directorios recursivo.

    Args:
        root: Directorio raiz.
        max_depth: Profundidad maxima de recursion.
        current_depth: Profundidad actual.

    Returns:
        Lista de nodos con name, type (dir/file) y children.
    """
    if current_depth >= max_depth:
        return []

    items = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return []

    skip_dirs = {".git", "node_modules", "__pycache__", ".gradle", "build", ".idea"}

    for entry in entries:
        if entry.name in skip_dirs:
            continue

        node = {"name": entry.name, "type": "dir" if entry.is_dir() else "file"}

        if entry.is_dir():
            node["children"] = _build_tree(entry, max_depth, current_depth + 1)

        items.append(node)

    return items


def _get_standards(stack: str) -> dict:
    """Obtiene los estandares del stack tecnologico.

    Args:
        stack: Identificador del stack (ej: java-spring-boot).

    Returns:
        Diccionario con categorias de estandares.
    """
    standards = {
        "java-spring-boot": {
            "stack_name": "Java 21 + Spring Boot 4.x + Gradle 9.x",
            "categories": [
                {
                    "name": "Naming",
                    "rules": [
                        {"rule": "Clases e Interfaces", "convention": "PascalCase", "example": "PolicyService, PolicyResponse"},
                        {"rule": "Metodos y Variables", "convention": "camelCase", "example": "findActivePolicy, policyId"},
                        {"rule": "Constantes", "convention": "UPPER_SNAKE_CASE", "example": "MAX_RETRY_ATTEMPTS"},
                        {"rule": "Booleanos", "convention": "is/has prefix", "example": "isActive, hasPermission"},
                        {"rule": "Paquetes", "convention": "lowercase", "example": "com.bolivar.gestion_polizas_ms"},
                        {"rule": "Archivos", "convention": "PascalCase.java", "example": "PolicyService.java"},
                    ],
                },
                {
                    "name": "Arquitectura",
                    "rules": [
                        {"rule": "Estructura", "convention": "Domain-driven (por modulo)", "example": "polizas/controller, polizas/services"},
                        {"rule": "Capas", "convention": "Controller → Service → Repository", "example": "Nunca logica en controller"},
                        {"rule": "DTOs", "convention": "Request/Response separados", "example": "CrearRequestDTO, ResponseDTO"},
                        {"rule": "Validacion", "convention": "Jakarta Validation + Pydantic-style", "example": "@NotNull, @Size, @Valid"},
                        {"rule": "Errores", "convention": "Excepciones especificas + handler global", "example": "PolicyNotFoundException"},
                        {"rule": "Inyeccion", "convention": "Constructor injection", "example": "private final PolicyRepository repo"},
                    ],
                },
                {
                    "name": "Testing",
                    "rules": [
                        {"rule": "Framework", "convention": "JUnit 5 + MockMvc", "example": "@SpringBootTest, @WebMvcTest"},
                        {"rule": "Patron", "convention": "Given / When / Then", "example": "Arrange → Act → Assert"},
                        {"rule": "Cobertura minima", "convention": "85% (JaCoCo)", "example": "Excluye: dto, config, models"},
                        {"rule": "Mocks", "convention": "Mockito + @MockBean", "example": "Nunca consumir backends reales"},
                        {"rule": "Nombres", "convention": "test_<accion>_<resultado>", "example": "test_getPolicy_returnsNotFound"},
                    ],
                },
                {
                    "name": "Seguridad",
                    "rules": [
                        {"rule": "Auth", "convention": "Spring Security + OAuth2 RS", "example": "JWT validado por IdP institucional"},
                        {"rule": "Autorizacion", "convention": "Backend siempre, nunca cliente", "example": "@PreAuthorize, ownership check"},
                        {"rule": "SQL", "convention": "Prepared statements (JPA)", "example": "Nunca concatenar queries"},
                        {"rule": "Secrets", "convention": "SSM Parameter Store", "example": "Nunca en codigo, siempre env/SSM"},
                        {"rule": "Headers", "convention": "HSTS, CSP, X-Frame-Options", "example": "SecurityHeaders config class"},
                        {"rule": "Tokens", "convention": "httpOnly cookies, no localStorage", "example": "SameSite=Strict"},
                    ],
                },
                {
                    "name": "Librerias Aprobadas",
                    "rules": [
                        {"rule": "ORM", "convention": "Spring Data JPA", "example": "JpaRepository, Specification"},
                        {"rule": "Validacion", "convention": "Jakarta Validation", "example": "@Valid, custom validators"},
                        {"rule": "Auth", "convention": "Spring Security", "example": "OAuth2ResourceServer"},
                        {"rule": "File Upload", "convention": "Spring Multipart", "example": "MultipartFile"},
                        {"rule": "Password Hash", "convention": "BCryptPasswordEncoder", "example": "strength 12"},
                        {"rule": "Testing", "convention": "JUnit 5 + MockMvc", "example": "Mockito, @WebMvcTest"},
                        {"rule": "Migrations", "convention": "Flyway / Liquibase", "example": "V1__init.sql"},
                        {"rule": "Build", "convention": "Gradle 8.x+", "example": "build.gradle.kts optional"},
                        {"rule": "DB Adapter", "convention": "HikariCP", "example": "Connection pooling"},
                    ],
                },
                {
                    "name": "CI/CD",
                    "rules": [
                        {"rule": "Pipeline", "convention": "GitHub Actions", "example": "pull-request.yml, pipeline.yaml"},
                        {"rule": "Quality Gate", "convention": "SonarCloud", "example": "0 critical/blocker, 80% coverage"},
                        {"rule": "Dependencias", "convention": "JFrog Artifactory", "example": "Nunca Maven Central directo"},
                        {"rule": "Docker", "convention": "Multi-stage build", "example": "eclipse-temurin:21-jre-alpine"},
                        {"rule": "Environments", "convention": "Dev, Stage, Prod separados", "example": "Nunca compartir BD entre envs"},
                    ],
                },
                {
                    "name": "Observabilidad",
                    "rules": [
                        {"rule": "APM", "convention": "Datadog Agent", "example": "dd-java-agent.jar"},
                        {"rule": "Logs", "convention": "Structured JSON + correlation_id", "example": "Logback + MDC"},
                        {"rule": "Metricas", "convention": "Micrometer + DogStatsD", "example": "Custom counters/gauges"},
                        {"rule": "Health", "convention": "Spring Actuator", "example": "/actuator/health"},
                        {"rule": "Tracing", "convention": "Distributed tracing (Datadog)", "example": "Correlation-ID en headers"},
                    ],
                },
            ],
        }
    }
    return standards.get(stack, {"stack_name": stack, "categories": []})


def _get_available_stacks() -> list:
    """Lista los stacks disponibles como templates.

    Returns:
        Lista de stacks con id, nombre y si tienen templates.
    """
    stacks = []
    if TEMPLATES_DIR.exists():
        for stack_dir in TEMPLATES_DIR.iterdir():
            if stack_dir.is_dir():
                stacks.append({
                    "id": stack_dir.name,
                    "name": stack_dir.name.replace("-", " ").title(),
                    "has_templates": True,
                    "template_count": sum(1 for _ in stack_dir.rglob("*.j2")),
                })
    return stacks


def _get_stack_blueprint(stack: str) -> str:
    """Lee el blueprint del stack.

    Args:
        stack: Identificador del stack.

    Returns:
        Contenido del blueprint como texto.
    """
    blueprint_file = BLUEPRINTS_DIR / "TECH_STACK_BLUEPRINT.md"
    if blueprint_file.exists():
        return blueprint_file.read_text(encoding="utf-8")
    return "Blueprint no encontrado."


# ─── ROUTES ──────────────────────────────────────────────────────────────────────


async def route_index(request: Request) -> HTMLResponse:
    """Sirve la UI HTML principal del visualizador."""
    html = UI_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html, status_code=200)


async def route_admin(request: Request) -> HTMLResponse:
    """Sirve la UI HTML de administracion (formulario nuevo stack)."""
    html = ADMIN_UI_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html, status_code=200)


async def route_api_archetype(request: Request) -> JSONResponse:
    """API: arbol de directorios del ultimo proyecto generado."""
    state = _get_project_state()
    return JSONResponse(state)


async def route_api_standards(request: Request) -> JSONResponse:
    """API: estandares del stack tecnologico."""
    stack = request.query_params.get("stack", "java-spring-boot")

    # Primero intentar leer guidelines aplicados (tienen prioridad)
    applied_file = Path("/settings/guidelines") / stack / "applied-guidelines.json"
    if applied_file.exists():
        try:
            applied = json.loads(applied_file.read_text(encoding="utf-8"))
            return JSONResponse(applied)
        except (json.JSONDecodeError, OSError):
            pass

    # Fallback a standards hardcoded
    standards = _get_standards(stack)
    return JSONResponse(standards)


async def route_api_stacks(request: Request) -> JSONResponse:
    """API: lista de stacks disponibles."""
    stacks = _get_available_stacks()
    return JSONResponse({"stacks": stacks})


async def route_api_blueprint(request: Request) -> JSONResponse:
    """API: blueprint tecnico del stack."""
    stack = request.query_params.get("stack", "java-spring-boot")
    content = _get_stack_blueprint(stack)
    return JSONResponse({"stack": stack, "content": content})


async def route_api_config(request: Request) -> JSONResponse:
    """API: configuracion y decisiones del ultimo proyecto."""
    state = _get_project_state()
    if state.get("status") != "ok":
        return JSONResponse(state)

    config = state.get("config", {})
    decisions = {
        "project_name": config.get("project_name"),
        "auth_strategy": config.get("auth_strategy"),
        "database": config.get("database", {}).get("db_name"),
        "modules": [m.get("module_name") for m in config.get("modules", [])],
        "integrations": {
            "s3": config.get("integrations", {}).get("uses_s3", False),
            "sqs": config.get("integrations", {}).get("uses_sqs", False),
            "soap": config.get("integrations", {}).get("uses_soap", False),
            "external_http": len(config.get("integrations", {}).get("external_http_services", [])),
        },
        "observability": config.get("observability", {}).get("datadog_enabled", True),
    }
    return JSONResponse({"decisions": decisions, "full_config": config})


async def route_api_guidelines_status(request: Request) -> JSONResponse:
    """API: estado de guidelines por stack."""
    guidelines_dir = Path("/settings/guidelines")
    stacks_status = []

    if guidelines_dir.exists():
        for stack_dir in guidelines_dir.iterdir():
            if stack_dir.is_dir():
                metadata_file = stack_dir / "metadata.json"
                applied_file = stack_dir / "applied-guidelines.json"
                status = {
                    "stack_id": stack_dir.name,
                    "has_raw": metadata_file.exists(),
                    "has_applied": applied_file.exists(),
                }
                if metadata_file.exists():
                    try:
                        meta = json.loads(metadata_file.read_text(encoding="utf-8"))
                        last = meta.get("last_ingestion", {})
                        status["last_ingested"] = last.get("ingested_at", "")
                        status["source_filename"] = last.get("source_filename", "")
                        status["ingestion_count"] = len(meta.get("ingestions", []))
                    except (json.JSONDecodeError, OSError):
                        pass
                if applied_file.exists():
                    try:
                        applied = json.loads(applied_file.read_text(encoding="utf-8"))
                        status["applied_at"] = applied.get("applied_at", "")
                        status["categories_count"] = len(applied.get("categories", []))
                        status["total_rules"] = sum(
                            len(c.get("rules", [])) for c in applied.get("categories", [])
                        )
                    except (json.JSONDecodeError, OSError):
                        pass
                stacks_status.append(status)

    return JSONResponse({"guidelines": stacks_status})


async def route_api_new_stack(request: Request) -> JSONResponse:
    """API: recibe formulario para registrar un nuevo stack.

    El formulario del admin UI envia los datos necesarios para
    scaffoldear la estructura de un nuevo stack.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "JSON invalido"}, status_code=400)

    stack_id = body.get("stack_id", "").strip()
    stack_name = body.get("stack_name", "").strip()
    runtime = body.get("runtime", "").strip()
    min_version = body.get("min_version", "").strip()
    description = body.get("description", "").strip()
    categories = body.get("categories", [])

    if not all([stack_id, stack_name, runtime, description]):
        return JSONResponse(
            {"status": "error", "message": "Campos requeridos: stack_id, stack_name, runtime, description"},
            status_code=400,
        )

    # Validar formato del stack_id
    import re
    if not re.match(r"^[a-z][a-z0-9-]+$", stack_id):
        return JSONResponse(
            {"status": "error", "message": "stack_id debe ser lowercase con guiones (ej: python-fastapi)"},
            status_code=400,
        )

    # Crear estructura del stack
    stack_dir = TEMPLATES_DIR / stack_id
    if stack_dir.exists():
        return JSONResponse(
            {"status": "error", "message": f"El stack '{stack_id}' ya existe en templates/"},
            status_code=409,
        )

    try:
        # Crear directorios base del stack
        dirs_to_create = [
            "src", "docs", "cicd", "git", "kiro",
            "kiro/hooks", "kiro/specs", "infra",
        ]
        for d in dirs_to_create:
            (stack_dir / d).mkdir(parents=True, exist_ok=True)

        # Crear README del stack
        readme_content = f"""# Stack: {stack_name}

## Runtime
- **Runtime:** {runtime}
- **Version minima:** {min_version}

## Descripcion
{description}

## Categorias de Templates
{chr(10).join(f'- {c}' for c in categories) if categories else '- (sin categorias definidas)'}

## Estado
- [ ] Templates base creados
- [ ] Generator implementado (src/generators/{stack_id.replace('-', '_')}.py)
- [ ] Registrado en list_available_stacks
- [ ] Blueprint documentado

## Como implementar

1. Crear templates Jinja2 en cada subcarpeta
2. Crear src/generators/{stack_id.replace('-', '_')}.py extendiendo BaseGenerator
3. Registrar en src/tools/list_available_stacks.py
4. Agregar blueprint en blueprints/
"""
        (stack_dir / "README.md").write_text(readme_content, encoding="utf-8")

        # Crear placeholder de blueprint
        blueprint_content = f"""# {stack_name} — Technical Blueprint

## Stack
- Runtime: {runtime} {min_version}+
- Description: {description}

## Patterns
(Pendiente de documentar)

## Conventions
(Pendiente de documentar)

## Libraries
(Pendiente de documentar)
"""
        blueprint_file = BLUEPRINTS_DIR / f"{stack_id.upper().replace('-', '_')}_BLUEPRINT.md"
        blueprint_file.write_text(blueprint_content, encoding="utf-8")

        # Crear placeholder del generator
        generator_name = stack_id.replace("-", "_")
        generator_content = f'''"""Generator para {stack_name}.

TODO: Implementar la logica de generacion para este stack.
"""

import logging
from pathlib import Path

from src.generators.base import BaseGenerator

logger = logging.getLogger("mcp_init_ms.generators.{generator_name}")


class {stack_name.replace(" ", "").replace("-", "")}Generator(BaseGenerator):
    """Generador de proyectos {stack_name}."""

    def generate(self) -> list[Path]:
        """Genera todos los archivos del proyecto.

        Returns:
            Lista de paths creados.
        """
        raise NotImplementedError(
            "Generator para '{stack_id}' aun no implementado. "
            "Crear templates en templates/{stack_id}/ y completar este generator."
        )
'''
        generators_dir = Path(__file__).parent.parent / "generators"
        (generators_dir / f"{generator_name}.py").write_text(generator_content, encoding="utf-8")

        logger.info("Nuevo stack creado: %s (%s)", stack_id, stack_name)

        return JSONResponse({
            "status": "success",
            "stack_id": stack_id,
            "message": f"Stack '{stack_name}' creado exitosamente.",
            "created": {
                "templates_dir": str(stack_dir),
                "blueprint": str(blueprint_file),
                "generator": f"src/generators/{generator_name}.py",
            },
            "next_steps": [
                f"1. Agregar templates Jinja2 en templates/{stack_id}/",
                f"2. Implementar la logica en src/generators/{generator_name}.py",
                "3. Registrar en src/tools/list_available_stacks.py",
                f"4. Completar el blueprint en blueprints/{stack_id.upper().replace('-', '_')}_BLUEPRINT.md",
            ],
        })
    except Exception as e:
        logger.exception("Error creando stack '%s'", stack_id)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ─── APP ─────────────────────────────────────────────────────────────────────────


app = Starlette(routes=[
    Route("/", route_index),
    Route("/admin", route_admin),
    Route("/api/archetype", route_api_archetype),
    Route("/api/standards", route_api_standards),
    Route("/api/stacks", route_api_stacks),
    Route("/api/blueprint", route_api_blueprint),
    Route("/api/config", route_api_config),
    Route("/api/guidelines/status", route_api_guidelines_status),
    Route("/api/stacks/new", route_api_new_stack, methods=["POST"]),
])


def start_visualizer() -> None:
    """Arranca el servidor de visualizacion en un thread en background."""
    def _run():
        logger.info("Archetype Visualizer arrancando en http://localhost:%d", VISUALIZER_PORT)
        uvicorn.run(app, host=VISUALIZER_HOST, port=VISUALIZER_PORT, log_level="warning")

    thread = threading.Thread(target=_run, daemon=True, name="archetype-visualizer")
    thread.start()
    logger.info("Archetype Visualizer thread iniciado (puerto %d)", VISUALIZER_PORT)
