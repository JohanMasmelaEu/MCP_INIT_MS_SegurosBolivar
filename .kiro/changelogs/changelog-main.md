# Changelog — main

## [No publicado]

### Agregado
- Se agregó tool `set_output_directory` para configurar una única vez el directorio de salida de proyectos generados
- Se agregó sistema de ingestion de lineamientos de stacks vía PDF/documentos:
  - Tool `ingest_stack_guidelines`: persiste el contenido crudo de un documento en `/settings/guidelines/<stack>/`
  - Tool `get_stack_guidelines`: recupera lineamientos (versión raw o applied) para análisis por el LLM de Kiro
  - Tool `apply_stack_guidelines`: persiste lineamientos refinados y aprobados por el usuario como documentación oficial
- Se agregó endpoint `/api/guidelines/status` en el visualizador para consultar estado de lineamientos por stack
- Se actualizó Admin UI (`/admin`) para mostrar estado de lineamientos ingresados (pendientes/aplicados, categorías, reglas)
- Se actualizó tab "Estándares" del Archetype Visualizer para priorizar guidelines aplicados sobre los hardcoded
- Se agregó módulo `src/utils/settings.py` para persistir configuración del MCP entre sesiones en volumen Docker `/settings`
- Se agregó volumen `/settings` en Dockerfile para persistencia de configuración
- Se agregó Archetype Visualizer UI en puerto 9752 (`src/engine/visualizer.py` + `visualizer_ui.html`)
  - Tab Arquetipo: árbol de directorios interactivo del proyecto generado
  - Tab Estándares: tabla de reglas por categoría (naming, arquitectura, testing, seguridad, libs, CI/CD, observabilidad)
  - Tab Decisiones: cards con las configuraciones elegidas (auth, DB, integraciones, módulos)
  - Tab Blueprint: texto completo del blueprint técnico del stack
- Se agregó Admin UI en `/admin` (`src/engine/admin_ui.html`) con formulario para registrar nuevos stacks tecnológicos
  - Crea estructura de directorios en `templates/<stack>/`
  - Genera blueprint placeholder en `blueprints/`
  - Genera generator placeholder en `src/generators/`
  - Muestra stacks existentes con conteo de templates
- Se agregó MCP Marketplace en `get_required_inputs` — catálogo de MCP Servers disponibles con descripciones y capabilities
  - MCP_INIT_MS_SegurosBolivar (auto-incluido): extensión de proyectos desde Kiro
  - MCP_HU_SegurosBolivar (opcional): análisis de historias de usuario con panel de expertos
- Se agregó modelo `McpServerSelection` en `project_config.py` y campo `selected_mcps` en `ProjectConfig`
- Se agregaron 4 hooks por stack Java Spring Boot generados automáticamente en proyectos:
  - `compile-on-save.json`: compila al guardar archivos .java
  - `test-after-task.json`: ejecuta tests al completar una tarea de spec
  - `code-standards-check.json`: verifica estándares de código antes de escribir archivos
  - `security-review.json`: revisa archivos de seguridad/configuración al guardarlos
- Se agregó template `.kiro/settings/mcp.json.j2` que genera config de MCP servers según selección del marketplace
- Se agregó template `.kiro/specs/project-initialization.md.j2` que genera spec inicial con requirements, design y tasks del proyecto

### Cambiado
- Se modificó `initialize_project` para usar el directorio configurado como default cuando no se pasa `target_path`
- Se reemplazó volumen `/workspace` por `/repos` (bind mount) + `/settings` (volumen nombrado) en Dockerfile
- Se actualizó `server.py` para registrar tool `set_output_directory`, hacer `target_path` opcional, y arrancar visualizador en boot
- Se actualizó `java_spring_boot.py` generator: ahora genera hooks, mcp.json y specs en `_generate_kiro_context()`
- Se actualizó `initialize_project.py` para notificar al visualizador tras generar un proyecto
- Se actualizó README con configuración Docker correcta, diagrama de arquitectura y documentación completa
- Se eliminó variable de entorno `MCP_WORKSPACE_PATH` del Dockerfile (ya no es necesaria)
- Se expone puerto 9752 en Dockerfile para el Archetype Visualizer

### Agregado
- Se agregó soporte multi-stack: Node.js/Express y Python/FastAPI junto al existente Java/Spring Boot
- Se actualizó `list_available_stacks.py` — los 3 stacks ahora tienen status 'available' con capabilities completas
- Se agregó categoría `node_specific` en `get_required_inputs.py` (typescript_strict, use_husky, npm_scope, use_npmrc)
- Se agregó categoría `python_specific` en `get_required_inputs.py` (mypy_strict, use_pre_commit)
- Se agregó campo `stack` a `ProjectConfig` (default: java-spring-boot)
- Se agregaron campos Node-specific a `ProjectConfig`: typescript_strict, use_husky, npm_scope, use_npmrc
- Se agregaron campos Python-specific a `ProjectConfig`: mypy_strict, use_pre_commit
- Se creó stub `src/generators/node_express.py` (NodeExpressGenerator) — pendiente Bloque B
- Se creó stub `src/generators/python_fastapi.py` (PythonFastApiGenerator) — pendiente Bloque C
- Se agregó file tree para Node/Express en `get_project_plan.py` (_build_node_file_tree)
- Se agregó file tree para Python/FastAPI en `get_project_plan.py` (_build_python_file_tree)

### Cambiado
- Se refactorizó `initialize_project.py` para usar dispatch dict `_GENERATORS` por stack en vez de hardcodear Java
- Se refactorizó `add_domain_module.py` para usar dispatch dict `_GENERATORS` por stack
- Se refactorizó `get_project_plan.py` — `_build_file_tree` delega a funciones por stack, `_build_next_steps` adapta pasos por stack
- Se actualizó `_flatten_categorized_config` en `server.py` para aplanar categorías node_specific y python_specific

### Agregado
- Se implementó generador completo `NodeExpressGenerator` en `src/generators/node_express.py`
- Se crearon 69 templates Jinja2 en `templates/node-express/` para generación completa de proyectos Node.js 22 + Express + TypeScript:
  - Core: package.json, tsconfig, vitest.config, eslint, prettier, git
  - Source: app.ts, server.ts, config/ (Zod env, Drizzle DB, Pino logger, Passport security), commons/, middleware/, errors/, utils/
  - Domain-module: controller (Router CRUD), service, repository (Drizzle), schema, DTOs (Zod), tests (Vitest+Supertest)
  - Infra: Dockerfile multi-stage, docker-compose (condicional Redis/OAuth/DD), seed-ssm, .env
  - CI/CD: pipeline GitHub Actions, CODEOWNERS, PR template
  - Docs: README completo, api_spec.yaml OpenAPI 3.0.3
  - Kiro: project.json, 10 steering files, 7 hooks, changelog, mcp-settings
  - Condicionales: husky pre-commit, .npmrc Artifactory, test-app helper

### Agregado
- Se implementó generador completo `PythonFastApiGenerator` en `src/generators/python_fastapi.py`
- Se crearon 72 templates Jinja2 en `templates/python-fastapi/` para generación completa de proyectos Python 3.12 + FastAPI + uv:
  - Core: pyproject.toml (uv + ruff + mypy + pytest), gitignore, pre-commit-config.yaml
  - Source: main.py (app factory con lifespan), config/ (Pydantic Settings, AsyncEngine SQLAlchemy, structlog, security condicional), commons/, middleware/, errors/, utils/
  - Domain-module: router (APIRouter CRUD con Depends DI), service, repository (SQLAlchemy async), models, schemas/ (Pydantic v2), tests/ (pytest + AsyncMock + httpx)
  - Infra: Dockerfile multi-stage (python:3.12-slim + uv), docker-compose condicional, seed-ssm, .env
  - CI/CD: pipeline GitHub Actions (uv + ruff + mypy + pytest), CODEOWNERS, PR template
  - Docs: README completo, api_spec.yaml OpenAPI 3.0.3
  - Kiro: project.json, 10 steering files, 7 hooks, changelog, mcp-settings
  - Tests base: conftest con httpx AsyncClient, factories

### Agregado
- Se implementó Implementation Tracker transversal para los 3 stacks:
  - Template `kiro/implementation-log.json.j2` en java-spring-boot, node-express y python-fastapi
  - Generadores actualizados para producir `.kiro/implementation-log.json` en cada proyecto generado
  - Sección "Implementation Tracker" agregada al steering `05-responsible-ai-use.md.j2` (reglas de tracking)
  - Hook `implementation-tracker.json.j2` (PostToolUse, registra progreso silenciosamente)
  - Hook `summary-on-completion.json.j2` actualizado para reportar estado del plan activo al finalizar sesión
