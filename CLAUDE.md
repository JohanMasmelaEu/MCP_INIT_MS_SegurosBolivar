# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An MCP (Model Context Protocol) server that generates complete Java 21 / Spring Boot 4.x / Gradle microservice archetypes for Seguros Bolivar. It runs inside a Docker container, communicates via stdio with Kiro IDE (or any MCP-compatible client), and writes generated projects to a bind-mounted host directory.

## Build & Run

```bash
# Build Docker image (--network=host needed for corporate VPN/PyPI access)
docker build --network=host -t mcp-init-ms-segurosbolivar:latest .

# Run locally for testing (stdio transport)
python -m src.server

# The server is NOT run manually in production — Kiro manages the container lifecycle
```

There are no tests or linting commands configured. Dependencies are in `requirements.txt` (mcp, pydantic, jinja2, click, uvicorn, starlette).

## Architecture

**Entry point:** `src/server.py` — creates a `FastMCP` instance, registers 11 tools as async handlers, and starts the Archetype Visualizer (Starlette HTTP on port 9752) in a background thread.

**Core flow:** User conversation in Kiro → `get_required_inputs` (9-category schema) → `get_project_plan` (preview) → `initialize_project` (generation). Each tool in `src/tools/` delegates to handler functions that orchestrate models, generators, and utilities.

**Key layers:**

- `src/tools/` — MCP tool handlers. Each file is one tool (or group: `stack_guidelines.py` has ingest/get/apply).
- `src/models/project_config.py` — Pydantic models (`ProjectConfig` is the root). Validates all user input. Contains derived properties (`base_package`, `application_class_name`, `ssm_app_prefix`, etc.) used extensively in templates. Includes metadata fields: `i18n` (active languages), `cache` (e.g. redis), `docker_profile` (image profile).
- `src/generators/base.py` — Abstract `BaseGenerator` with `generate()`, `generate_domain_module()`, `regenerate_infrastructure()`.
- `src/generators/java_spring_boot.py` — `JavaSpringBootGenerator`, the only concrete generator. Builds a template context dict from `ProjectConfig`, then renders Jinja2 templates via `TemplateRenderer` and writes them via `FileWriter`. The `_generate_kiro_context()` method produces the complete `.kiro/` workspace (project.json + 10 steering files + 7 hooks + changelog).
- `src/utils/template_renderer.py` — Jinja2 environment with custom filters (e.g., `java_type_import`, `to_camel_case`, `to_pascal_case`, `to_snake_case`, `to_upper_snake`, `pluralize_es`). Templates live in `templates/<stack-id>/`.
- `src/utils/file_writer.py` — Writes files to `project_root`, tracks created files list.
- `src/utils/settings.py` — Persists output directory config to `/settings` volume (survives container restarts).
- `src/engine/visualizer.py` — Starlette app serving an admin UI and archetype visualizer at `localhost:9752`. Exposes REST APIs (`/api/archetype`, `/api/standards`, `/api/stacks`, etc.).

**Templates:** `templates/java-spring-boot/` contains Jinja2 `.j2` files organized by concern:

- `gradle/` — build.gradle, settings, wrapper
- `src/` — Java base: commons, config, config/security, entity, errorhandling, utils
- `domain-module/` — repeatable template set per CRUD module (controller, DTOs, service interface+impl, repository, specification, entity, tests)
- `resources/` — application.yaml (3 profiles: default, local, test)
- `infra/` — Dockerfile, docker-compose, LocalStack seed, mock-oauth, env
- `cicd/` — GitHub Actions pipelines, CODEOWNERS, PR template
- `docs/` — README, api_spec.yaml
- `kiro/` — Complete Kiro workspace:
  - `project.json.j2` — project metadata (stack, dockerProfile, cache, i18n)
  - `steering/` — 10 files (00-org-conventions through 10-stack-java) with organizational, architecture, security, code-style, testing, responsible-AI-use, data-access, error-handling, observability, and stack-specific rules
  - `hooks/` — 7 hooks: pre-write-gate (plan+architecture+scope gate), responsible-use (prompt validation), code-review-gate (post-write review), test-coverage-gate, build-validate (compile on save), integrity-check (session start), summary-on-completion
  - `changelog-develop.md.j2`, `mcp-settings.json.j2`, `specs/`

**Design document:** `CONSOLIDADO_DISENO_MCP.md` contains the full specification for all steering and hook content. Steering file content must be copied from this document — never invented.

**Rules:** `rules/` contains transversal markdown files (architecture, security, code-style, tech-stack, changelog). These are reference documents for the MCP project itself; the generated projects receive their rules via the steering templates in `templates/java-spring-boot/kiro/steering/`.

## Adding a New Stack

1. Create `templates/<new-stack>/` with Jinja2 templates
2. Create `src/generators/<new_stack>.py` extending `BaseGenerator`
3. Register in `src/tools/list_available_stacks.py`
4. Add blueprint in `blueprints/`

The admin UI at `/admin` can scaffold this structure via `POST /api/stacks/new`.

## Constraints

- Project names must match `^[a-z][a-z0-9-]+-ms$` (end with `-ms`)
- All paths inside the container use `/repos/...` (bind-mounted from host)
- Settings persist in `/settings` volume, not in the app directory
- The server never calls external LLMs — Kiro is the intelligence layer
- Generation always requires user confirmation (plan → approve → generate)
- Dependencies must come from JFrog Artifactory with pinned versions (no `^`, `*`, `latest`)

## Conventions (Generated Projects)

- Domain-driven structure: each module gets its own package (`controller/`, `dto/`, `services/`, `repository/`)
- Auth strategies: `oauth2-resource-server`, `api-gateway-delegated`, `machine-to-machine`, `deferred`
- Changelog in Spanish with categories: Agregado, Cambiado, Obsoleto, Eliminado, Corregido, Seguridad
- API versioning via route prefix (`/api/v1/...`)
- JaCoCo minimum 85% coverage
- CI/CD via GitHub Actions with institutional templates
- i18n: default Spanish only; English opt-in via `project.json.i18n`
- Cache: optional Redis via `project.json.cache`
- Docker profile: indexed in `project.json.dockerProfile` for the container image repo
