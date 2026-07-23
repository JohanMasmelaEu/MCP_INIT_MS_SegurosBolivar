# Schedule de Implementación V3 — Stacks Node/Express + Python/FastAPI

## Instrucciones para el agente ejecutor

**LEER PRIMERO ANTES DE EJECUTAR:**

1. Este schedule es autocontenido. Todo lo necesario para implementar está aquí + los blueprints.
2. Los archivos de referencia que debes leer antes de empezar:
   - `CONSOLIDADO_DISENO_MCP.md` — diseño general del MCP y convenciones
   - `blueprints/TECH_STACK_BLUEPRINT_NODE.md` — patrones, código ejemplo, estructura para Node
   - `blueprints/TECH_STACK_BLUEPRINT_PYTHON.md` — patrones, código ejemplo, estructura para Python
   - `src/generators/java_spring_boot.py` — generador existente de Java (usar como REFERENCIA de estructura, no copiar lógica)
   - `templates/java-spring-boot/` — templates existentes (referencia de cómo se parametrizan con Jinja2)
3. **NO modificar nada de Java** salvo los archivos compartidos indicados en bloque A.
4. **NO inventar patrones** — usar exactamente lo que dicen los blueprints.
5. Verificar sintaxis Python después de cada task del bloque A con: `python -c "import ast; ast.parse(open('archivo.py','r',encoding='utf-8').read()); print('OK')"`
6. Los templates Jinja2 no se pueden verificar con Python (no son .py), solo verificar que existan.

## Estado actual del proyecto

- **Archivos Python clave (ya existentes):**
  - `src/server.py` — entry point MCP, registra tools, tiene `_parse_config` + `_flatten_categorized_config`
  - `src/models/project_config.py` — modelo Pydantic con TODOS los campos (app_port, cache, auth_strategy, etc.)
  - `src/generators/base.py` — clase abstracta `BaseGenerator` que los generadores extienden
  - `src/generators/java_spring_boot.py` — generador Java (REFERENCIA de cómo implementar)
  - `src/tools/initialize_project.py` — instancia el generador según el stack
  - `src/tools/get_required_inputs.py` — schema de inputs (ya tiene 12 categorías para Java)
  - `src/tools/get_project_plan.py` — genera preview del file tree
  - `src/tools/add_domain_module.py` — agrega módulo a proyecto existente
  - `src/utils/template_renderer.py` — motor Jinja2 con filtros custom
  - `src/utils/file_writer.py` — escritura segura de archivos

- **Templates existentes (solo Java):**
  - `templates/java-spring-boot/` — ~60 templates Jinja2
  - Subdirs: gradle/, git/, src/, domain-module/, resources/, infra/, cicd/, docs/, kiro/

- **Blueprints (referencia de patrones):**
  - `blueprints/TECH_STACK_BLUEPRINT.md` — Java (ya implementado)
  - `blueprints/TECH_STACK_BLUEPRINT_NODE.md` — Node (POR implementar)
  - `blueprints/TECH_STACK_BLUEPRINT_PYTHON.md` — Python (POR implementar)

## Decisiones técnicas ya tomadas (NO cambiar)

| Aspecto | Java | Node | Python |
|---------|------|------|--------|
| Runtime | JDK 21 | Node.js 22 + TypeScript 5.5 | Python 3.12 |
| Package manager | Gradle 9.4 | npm 10.x | uv |
| Framework | Spring Boot 4.0 | Express 4.21 | FastAPI 0.115 |
| ORM | Spring Data JPA + Specification | Drizzle ORM | SQLAlchemy 2.x async |
| Validación | Jakarta Validation | Zod | Pydantic v2 |
| Auth | Spring Security | Passport JWT | python-jose + FastAPI Depends |
| Logger | Logback + MDC | Pino + AsyncLocalStorage | structlog + contextvars |
| Test runner | JUnit 5 + Mockito | Vitest + Supertest + nock | pytest + httpx + respx |
| Linter | (IDE/SonarQube) | ESLint v9 flat + Prettier | Ruff (lint+format+isort+bandit) |
| Type checker | (compilador Java) | TypeScript strict | mypy strict |
| Pre-commit | N/A | Husky + lint-staged (default, preguntable) | pre-commit (default, preguntable) |
| Coverage tool | JaCoCo (85%) | vitest --coverage v8 (80%) | pytest-cov (80%) |
| Puerto default | 8080 | 3000 | 8000 |
| Swagger UI | springdoc-openapi | swagger-ui-express + api_spec.yaml | FastAPI /docs redirigido a path custom + api_spec.yaml |
| Docker base | eclipse-temurin:21 | node:22-alpine | python:3.12-slim |
| Migraciones | NO (repo BD es dueño) | NO | NO |

## Convenciones transversales (aplican a los 3)

- Naming proyecto: `kebab-case-ms`
- Respuesta API: `{codigo, mensaje, data}`
- Paginación: `{content, page, size, totalPages, totalElements}`
- 4 auth strategies: oauth2-resource-server, api-gateway-delegated, machine-to-machine, deferred
- Docker Compose: LocalStack + Redis(condicional) + mock-oauth(condicional) + Datadog(condicional)
- Puertos dinámicos (`app_port`, `localstack_port`, `redis_port`)
- Coverage 80% min (parametrizable)
- Sin migraciones (repo BD es dueño del schema)
- Steering y hooks de Kiro IDÉNTICOS (solo cambia stack name y build-validate cmd)
- Implementation Tracker: `.kiro/implementation-log.json`
- Módulo dominio: controller/router + service + repository + model/schema + DTOs + 2 tests

---

## BLOQUE A: Infraestructura compartida (afecta los 3 stacks)

### TASK A1 — Actualizar list_available_stacks

**Archivo:** `src/tools/list_available_stacks.py`

**Cambio:** Agregar Node y Python a la lista:

```python
return {
    "stacks": [
        {
            "id": "java-spring-boot",
            "name": "Java 21 + Spring Boot 4.x + Gradle 9.x",
            "status": "available",
            "description": "...",
            "version": "1.0.0",
        },
        {
            "id": "node-express",
            "name": "Node.js 22 + Express 4.x + TypeScript 5.x",
            "status": "available",
            "description": (
                "Microservicio Node.js con Express, TypeScript strict, Drizzle ORM (PostgreSQL), "
                "Zod validation, Pino logging, Passport JWT, Docker Compose local "
                "(LocalStack + Redis + Datadog Agent no-forward), Vitest + Supertest, "
                "CI/CD GitHub Actions."
            ),
            "version": "1.0.0",
        },
        {
            "id": "python-fastapi",
            "name": "Python 3.12 + FastAPI + uv",
            "status": "available",
            "description": (
                "Microservicio Python con FastAPI, SQLAlchemy 2.x async (PostgreSQL), "
                "Pydantic v2, structlog, uv package manager, Docker Compose local "
                "(LocalStack + Redis + Datadog Agent no-forward), pytest + httpx, "
                "Ruff + mypy, CI/CD GitHub Actions."
            ),
            "version": "1.0.0",
        },
    ],
}
```

---

### TASK A2 — Actualizar get_blueprint para reconocer los 3 stacks

**Archivo:** `src/tools/get_blueprint.py`

**Cambio:** Mapear stack_id a archivo de blueprint:

```python
BLUEPRINT_MAP = {
    "java-spring-boot": "TECH_STACK_BLUEPRINT.md",
    "node-express": "TECH_STACK_BLUEPRINT_NODE.md",
    "python-fastapi": "TECH_STACK_BLUEPRINT_PYTHON.md",
}
```

Reemplazar el `if stack != "java-spring-boot"` por lookup en el map.

---

### TASK A3 — Actualizar get_required_inputs para soportar Node y Python

**Archivo:** `src/tools/get_required_inputs.py`

**Cambio:** El stack determina qué categorías se muestran. Categorías comunes a todos:
- project_identity, domain_modules, database, authentication, security_details, integrations, observability, ports, localstack, artifactory, mcp_marketplace, project_metadata

**Categorías adicionales por stack:**

Para `node-express`:
```python
def _node_specific_category() -> dict:
    return {
        "name": "node_specific",
        "label": "Configuracion Node.js",
        "fields": [
            {
                "key": "typescript_strict",
                "label": "TypeScript strict mode",
                "type": "boolean",
                "default": True,
                "description": "strict:true en tsconfig. Default recomendado. Desactivar solo si hay razón técnica justificada.",
            },
            {
                "key": "use_husky",
                "label": "Incluir Husky + lint-staged (pre-commit hooks)",
                "type": "boolean",
                "default": True,
                "description": (
                    "Si se habilita: ESLint + Prettier corren automáticamente en cada commit sobre los archivos staged. "
                    "Previene que código con errores de lint llegue al PR. "
                    "Si se deshabilita: el linting solo ocurre en CI (pipeline) o manualmente. "
                    "Código con errores podría llegar al PR y ser rechazado allí."
                ),
            },
            {
                "key": "npm_scope",
                "label": "Scope npm (ej: @bolivar)",
                "type": "string",
                "required": False,
                "default": None,
                "description": "Si se indica, el package.json usa ese scope. Si no, queda sin scope.",
            },
            {
                "key": "use_npmrc",
                "label": "Generar .npmrc con registry Artifactory",
                "type": "boolean",
                "default": False,
                "description": "Genera .npmrc apuntando a Artifactory institucional. Activar si el proyecto usa dependencias privadas @bolivar.",
            },
        ],
    }
```

Para `python-fastapi`:
```python
def _python_specific_category() -> dict:
    return {
        "name": "python_specific",
        "label": "Configuracion Python",
        "fields": [
            {
                "key": "mypy_strict",
                "label": "mypy strict mode",
                "type": "boolean",
                "default": True,
                "description": "mypy --strict en config. Default recomendado. Desactivar solo si hay razón técnica justificada.",
            },
            {
                "key": "use_pre_commit",
                "label": "Incluir pre-commit hooks (ruff + mypy en staged files)",
                "type": "boolean",
                "default": True,
                "description": (
                    "Si se habilita: ruff + mypy corren automáticamente en cada commit sobre los archivos staged. "
                    "Previene que código con errores llegue al PR. "
                    "Si se deshabilita: lint y type-check solo ocurren en CI o manualmente."
                ),
            },
        ],
    }
```

**Lógica:** `handle_get_required_inputs(stack)` retorna las categorías comunes + la categoría específica del stack.

---

### TASK A4 — Actualizar ProjectConfig con campos de Node y Python

**Archivo:** `src/models/project_config.py`

**Agregar campos opcionales** (solo aplican si el stack los usa):

```python
# --- Node specific ---
typescript_strict: bool = Field(default=True, description="TypeScript strict mode en tsconfig.")
use_husky: bool = Field(default=True, description="Incluir Husky + lint-staged para pre-commit.")
npm_scope: Optional[str] = Field(default=None, description="Scope npm (ej: @bolivar). None = sin scope.")
use_npmrc: bool = Field(default=False, description="Generar .npmrc con registry Artifactory.")

# --- Python specific ---
mypy_strict: bool = Field(default=True, description="mypy --strict en config.")
use_pre_commit: bool = Field(default=True, description="Incluir pre-commit hooks.")
```

---

### TASK A5 — Actualizar initialize_project y add_domain_module para instanciar el generador correcto

**Archivo:** `src/tools/initialize_project.py`

**Cambio:** En vez de hardcodear `JavaSpringBootGenerator`, elegir según un campo `stack` en config:

```python
from src.generators.java_spring_boot import JavaSpringBootGenerator
from src.generators.node_express import NodeExpressGenerator
from src.generators.python_fastapi import PythonFastApiGenerator

GENERATORS = {
    "java-spring-boot": JavaSpringBootGenerator,
    "node-express": NodeExpressGenerator,
    "python-fastapi": PythonFastApiGenerator,
}

# En handle_initialize_project:
stack = config_dict.get("stack", "java-spring-boot")
generator_class = GENERATORS.get(stack)
if not generator_class:
    return {"status": "error", "message": f"Stack '{stack}' no soportado."}
generator = generator_class(config, project_root)
```

**Mismo cambio en `src/tools/add_domain_module.py`.**

**Nota:** Agregar campo `stack` a ProjectConfig:
```python
stack: str = Field(default="java-spring-boot", description="Stack tecnológico del proyecto.")
```

---

### TASK A6 — Actualizar _flatten_categorized_config para nuevos campos

**Archivo:** `src/server.py`

**Agregar:**
```python
# node_specific → campos planos
if "node_specific" in config_dict:
    flat.update(config_dict["node_specific"])

# python_specific → campos planos
if "python_specific" in config_dict:
    flat.update(config_dict["python_specific"])
```

---

### TASK A7 — Actualizar get_project_plan para que sepa del stack

**Archivo:** `src/tools/get_project_plan.py`

**Cambio:** El file tree se genera según el stack. Refactorizar `_build_file_tree` para delegar al generador (o tener funciones por stack).

---

## BLOQUE B: Stack Node/Express

### TASK B1 — Crear generador NodeExpressGenerator

**Archivo a crear:** `src/generators/node_express.py`

**Clase:** `NodeExpressGenerator(BaseGenerator)` con métodos:
- `generate()` — genera proyecto completo
- `generate_domain_module(module)` — genera un módulo CRUD
- `regenerate_infrastructure()` — regenera docker-compose/env/seed

**Métodos internos (misma estructura que Java):**
- `_generate_package_json()` — con deps condicionales por auth/cache
- `_generate_tsconfig()` — strict mode configurable
- `_generate_git_files()` — .gitignore, .gitattributes
- `_generate_eslint_prettier()` — eslint.config.mjs, .prettierrc
- `_generate_src_base()` — app.ts, server.ts
- `_generate_config()` — config/index.ts, database.ts, logger.ts, security.ts
- `_generate_commons()` — api-response.dto.ts, pagination.dto.ts, audit.mixin.ts
- `_generate_middleware()` — error-handler, correlation-id, request-logger, validate, auth
- `_generate_errors()` — bolivar-business.error.ts, error-types.enum.ts
- `_generate_utils()` — data-sanitizer.ts, date.utils.ts
- `_generate_resources()` — (no aplica en Node, config es por env vars)
- `_generate_infrastructure()` — Dockerfile, docker-compose, seed-ssm, .env.sample (condicionales por auth/cache)
- `_generate_cicd()` — pipeline.yaml, CODEOWNERS, PR template
- `_generate_documentation()` — README.md, api_spec.yaml
- `_generate_kiro_context()` — steering, hooks, project.json, changelogs
- `_generate_husky()` — si use_husky=True: .husky/pre-commit, lint-staged config
- `_generate_npmrc()` — si use_npmrc=True: .npmrc con Artifactory
- `_generate_vitest_config()` — vitest.config.ts

**Contexto del template (variables disponibles en Jinja2):**
Todos los del Java + `typescript_strict`, `use_husky`, `npm_scope`, `use_npmrc`

---

### TASK B2 — Crear directorio de templates Node

**Directorio:** `templates/node-express/`

**Estructura de archivos a crear:**

```
templates/node-express/
├── package.json.j2
├── tsconfig.json.j2
├── vitest.config.ts.j2
├── eslint.config.mjs.j2
├── prettierrc.j2
├── npmrc.j2                          ← condicional (solo si use_npmrc)
├── git/
│   ├── gitignore.j2
│   └── gitattributes.j2
├── husky/
│   └── pre-commit.j2                ← condicional (solo si use_husky)
├── src/
│   ├── app.ts.j2
│   ├── server.ts.j2
│   ├── config/
│   │   ├── index.ts.j2              ← Zod schema para env vars
│   │   ├── database.ts.j2           ← Pool pg + Drizzle client
│   │   ├── logger.ts.j2             ← Pino instance
│   │   └── security.ts.j2           ← Passport strategies
│   ├── commons/
│   │   ├── api-response.dto.ts.j2
│   │   ├── pagination.dto.ts.j2
│   │   └── audit.mixin.ts.j2
│   ├── middleware/
│   │   ├── error-handler.ts.j2
│   │   ├── correlation-id.ts.j2
│   │   ├── request-logger.ts.j2
│   │   ├── validate.ts.j2
│   │   └── auth.ts.j2               ← condicional por auth_strategy
│   ├── errors/
│   │   ├── bolivar-business.error.ts.j2
│   │   └── error-types.enum.ts.j2
│   └── utils/
│       ├── data-sanitizer.ts.j2
│       └── date.utils.ts.j2
├── domain-module/
│   ├── controller.ts.j2
│   ├── service.ts.j2
│   ├── repository.ts.j2
│   ├── schema.ts.j2                 ← Drizzle table definition
│   ├── dto/
│   │   ├── crear.dto.ts.j2
│   │   ├── actualizar.dto.ts.j2
│   │   ├── filtros.dto.ts.j2
│   │   └── response.dto.ts.j2
│   └── tests/
│       ├── service.test.ts.j2
│       └── controller.test.ts.j2
├── tests/
│   └── helpers/
│       └── test-app.ts.j2           ← Express app sin listen (para supertest)
├── infra/
│   ├── Dockerfile.j2
│   ├── docker-compose.yml.j2
│   ├── seed-localstack-ssm.sh.j2
│   ├── mock-oauth-config.json.j2    ← condicional
│   ├── env.sample.j2
│   └── env.j2
├── cicd/
│   ├── pipeline.yaml.j2
│   ├── CODEOWNERS.j2
│   └── pull_request_template.md.j2
├── docs/
│   ├── README.md.j2
│   └── api_spec.yaml.j2
└── kiro/
    ├── project.json.j2
    ├── changelog-develop.md.j2
    ├── steering/
    │   └── (mismos 00-08 que Java + 10-stack-node.md)
    └── hooks/
        └── (mismos 7 hooks que Java, build-validate usa npm run lint)
```

**Total estimado: ~45 templates**

---

### TASK B3 — Escribir cada template con contenido real

Cada template debe seguir los patrones definidos en el blueprint (`TECH_STACK_BLUEPRINT_NODE.md`). Los templates más críticos son:

1. **package.json.j2** — deps condicionales por auth (passport-jwt solo si oauth2-rs), cache (ioredis si redis), scope dinámico, scripts completos
2. **docker-compose.yml.j2** — misma lógica que Java (puertos dinámicos, redis condicional, mock-oauth condicional) pero imagen node:22-alpine
3. **Dockerfile.j2** — multi-stage: build con npm ci + tsc, runtime con solo dist/ + node_modules prod
4. **src/app.ts.j2** — configura Express con middlewares condicionales (helmet, cors, auth)
5. **domain-module/controller.ts.j2** — CRUD completo con Router, validate middleware, paginación
6. **src/config/security.ts.j2** — Passport strategies condicionales por auth_strategy

**Criterio de contenido:** Copiar patrones del blueprint, hacerlos dinámicos con variables Jinja2 donde aplique.

---

## BLOQUE C: Stack Python/FastAPI

### TASK C1 — Crear generador PythonFastApiGenerator

**Archivo a crear:** `src/generators/python_fastapi.py`

**Clase:** `PythonFastApiGenerator(BaseGenerator)` con métodos:
- `generate()` — genera proyecto completo
- `generate_domain_module(module)` — genera un módulo CRUD
- `regenerate_infrastructure()` — regenera docker-compose/env/seed

**Métodos internos:**
- `_generate_pyproject()` — pyproject.toml con deps condicionales por auth/cache
- `_generate_git_files()` — .gitignore
- `_generate_ruff_config()` — (va dentro de pyproject.toml)
- `_generate_src_base()` — main.py (app factory)
- `_generate_config()` — settings.py, database.py, logging.py, security.py
- `_generate_commons()` — api_response.py, pagination.py, audit_mixin.py
- `_generate_middleware()` — correlation_id, error_handler, request_logger, security_headers
- `_generate_errors()` — bolivar_business_error.py, error_types.py
- `_generate_utils()` — data_sanitizer.py, date_utils.py
- `_generate_tests_base()` — conftest.py con fixtures
- `_generate_infrastructure()` — Dockerfile, docker-compose, seed-ssm, .env.sample (condicionales)
- `_generate_cicd()` — pipeline.yaml, CODEOWNERS, PR template
- `_generate_documentation()` — README.md, api_spec.yaml
- `_generate_kiro_context()` — steering, hooks, project.json, changelogs
- `_generate_pre_commit()` — si use_pre_commit=True: .pre-commit-config.yaml

---

### TASK C2 — Crear directorio de templates Python

**Directorio:** `templates/python-fastapi/`

**Estructura:**

```
templates/python-fastapi/
├── pyproject.toml.j2
├── git/
│   └── gitignore.j2
├── pre-commit/
│   └── pre-commit-config.yaml.j2    ← condicional
├── src/
│   ├── __init__.py.j2
│   ├── main.py.j2                    ← app factory + include_router
│   ├── config/
│   │   ├── __init__.py.j2
│   │   ├── settings.py.j2           ← Pydantic Settings (env vars)
│   │   ├── database.py.j2           ← AsyncEngine + AsyncSession
│   │   ├── logging.py.j2            ← structlog config
│   │   └── security.py.j2           ← JWT decode, auth dependencies
│   ├── commons/
│   │   ├── __init__.py.j2
│   │   ├── api_response.py.j2
│   │   ├── pagination.py.j2
│   │   └── audit_mixin.py.j2
│   ├── middleware/
│   │   ├── __init__.py.j2
│   │   ├── correlation_id.py.j2
│   │   ├── error_handler.py.j2
│   │   ├── request_logger.py.j2
│   │   └── security_headers.py.j2
│   ├── errors/
│   │   ├── __init__.py.j2
│   │   ├── bolivar_business_error.py.j2
│   │   └── error_types.py.j2
│   └── utils/
│       ├── __init__.py.j2
│       ├── data_sanitizer.py.j2
│       └── date_utils.py.j2
├── domain-module/
│   ├── __init__.py.j2
│   ├── router.py.j2
│   ├── service.py.j2
│   ├── repository.py.j2
│   ├── models.py.j2                  ← SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py.j2
│   │   ├── crear.py.j2
│   │   ├── actualizar.py.j2
│   │   ├── filtros.py.j2
│   │   └── response.py.j2
│   └── tests/
│       ├── test_service.py.j2
│       └── test_router.py.j2
├── tests/
│   ├── __init__.py.j2
│   ├── conftest.py.j2                ← fixtures: app, client, db_session
│   └── factories/
│       └── __init__.py.j2
├── infra/
│   ├── Dockerfile.j2
│   ├── docker-compose.yml.j2
│   ├── seed-localstack-ssm.sh.j2
│   ├── mock-oauth-config.json.j2    ← condicional
│   ├── env.sample.j2
│   └── env.j2
├── cicd/
│   ├── pipeline.yaml.j2
│   ├── CODEOWNERS.j2
│   └── pull_request_template.md.j2
├── docs/
│   ├── README.md.j2
│   └── api_spec.yaml.j2
└── kiro/
    ├── project.json.j2
    ├── changelog-develop.md.j2
    ├── steering/
    │   └── (mismos 00-08 que Java + 10-stack-python.md)
    └── hooks/
        └── (mismos 7 hooks, build-validate usa ruff check src/)
```

**Total estimado: ~50 templates** (más __init__.py por paquete)

---

### TASK C3 — Escribir cada template con contenido real

Templates críticos:

1. **pyproject.toml.j2** — deps condicionales por auth/cache, config de ruff/mypy/pytest, scripts
2. **docker-compose.yml.j2** — misma lógica que Java/Node pero imagen python:3.12-slim + uv
3. **Dockerfile.j2** — multi-stage con uv: build deps + copy src, runtime slim
4. **src/main.py.j2** — app factory con lifespan, include_router por dominio, middleware condicional
5. **domain-module/router.py.j2** — CRUD completo con Depends, Pydantic schemas, paginación
6. **domain-module/repository.py.j2** — SQLAlchemy async con filtros composables (Specification-like)
7. **tests/conftest.py.j2** — fixtures de app, client httpx, AsyncSession

---

## BLOQUE D: Verificación final

### TASK D1 — Verificar que los 3 stacks generan sin error

Generar un proyecto de prueba con cada stack:

```python
# Java (ya funciona, verificar que no se rompió)
config_java = {"stack": "java-spring-boot", "project_name": "test-java-ms", ...}

# Node
config_node = {"stack": "node-express", "project_name": "test-node-ms", ...}

# Python
config_python = {"stack": "python-fastapi", "project_name": "test-python-ms", ...}
```

Verificar para cada uno:
- [ ] Genera sin error
- [ ] Archivos correctos para el stack (no mezcla Java con Node)
- [ ] auth_strategy condicional funciona (probar M2M → no genera OAuth)
- [ ] cache=redis genera servicio Redis en compose + dependencia + config
- [ ] Puertos dinámicos funcionan
- [ ] Steering y hooks se generan idénticos (solo stack name diferente)
- [ ] add_domain_module funciona post-generación

### TASK D2 — Actualizar README del MCP

Agregar los nuevos stacks a la documentación:
- Sección "Qué genera" mencionar los 3 stacks
- Actualizar tabla de tools con nota de multi-stack

---

## ORDEN DE EJECUCIÓN

```
A1 → A2 → A3 → A4 → A5 → A6 → A7  (infraestructura, ~1 sesión)
B1 → B2 → B3                        (Node completo, ~2-3 sesiones)
C1 → C2 → C3                        (Python completo, ~2-3 sesiones)
D1 → D2                             (verificación, ~1 sesión)
```

Tasks del bloque A son prerequisitos para B y C.
B y C son independientes entre sí (se pueden paralelizar).
D requiere que B y C estén completos.

---

## NOTAS PARA EL AGENTE EJECUTOR

1. **Los templates de kiro/ (steering, hooks) son IDÉNTICOS a los de Java** — copiar y solo cambiar: `10-stack-java.md` → `10-stack-node.md` o `10-stack-python.md`, y el comando de `build-validate.json` (`npm run lint` para Node, `ruff check src/` para Python).

2. **docker-compose.yml.j2 tiene la MISMA lógica condicional que Java** — solo cambia la sección `app:` (imagen, puertos internos, ENTRYPOINT). Reusable al 90%.

3. **El contenido de cada template viene del blueprint correspondiente** (`TECH_STACK_BLUEPRINT_NODE.md` o `TECH_STACK_BLUEPRINT_PYTHON.md`). No inventar — copiar patrones del blueprint y parametrizar con Jinja2.

4. **`__init__.py` en Python** — la mayoría son archivos vacíos. Crear un template `__init__.py.j2` con solo un docstring y reusar.

5. **El campo `stack` en ProjectConfig** determina qué generador se instancia. Se agrega al flatten como campo plano que viene de `project_identity` o del primer nivel.

6. **Puerto default por stack:** Java=8080, Node=3000, Python=8000. El campo `app_port` ya existe en ProjectConfig — solo ajustar el default según el stack elegido en la lógica del generador (no en el modelo).


---

## BLOQUE E: Implementation Tracker (transversal, todos los stacks)

### TASK E1 — Crear template del implementation-log.json

**Archivo a crear:** Template en cada stack:
- `templates/java-spring-boot/kiro/implementation-log.json.j2`
- `templates/node-express/kiro/implementation-log.json.j2`
- `templates/python-fastapi/kiro/implementation-log.json.j2`

(Los 3 son idénticos — es un archivo transversal)

**Contenido del template:**

```jinja2
{
  "version": "1.0",
  "project": "{{ project_name }}",
  "stack": "{{ c.stack }}",
  "created_at": "{{ now_iso }}",
  "plans": []
}
```

---

### TASK E2 — Actualizar generadores para producir implementation-log.json

En `_generate_kiro_context()` de cada generador, agregar:

```python
self._render_write("kiro/implementation-log.json.j2", ".kiro/implementation-log.json", ctx_with_date)
```

---

### TASK E3 — Actualizar steering 05-responsible-ai-use.md

Agregar sección al steering que instruye al agente sobre el tracker:

```markdown
## Implementation Tracker (.kiro/implementation-log.json)

### Reglas
- Cuando el usuario aprueba un plan completo, registrar el plan en el tracker
  con sus tareas, timestamps y status.
- Al iniciar cada tarea del plan, registrar started_at.
- Al completar cada tarea, registrar completed_at + files_modified + lines_added/removed.
- Al finalizar la sesión, recalcular metrics del plan activo.
- NUNCA borrar planes anteriores — el archivo es append-only.
- Si la sesión termina con tareas pendientes, el plan queda en "in_progress".
- Al iniciar una nueva sesión, verificar si hay planes in_progress y retomar.

### Formato
El archivo es JSON machine-readable. Otros MCPs/agentes pueden leerlo para:
- Saber qué se implementó y qué falta
- Estimar esfuerzo futuro basado en historial
- Detectar planes olvidados con tareas pendientes
- Cruzar con changelog para auditoría
```

---

### TASK E4 — Crear/actualizar hook para alimentar el tracker

**Nuevo hook: `implementation-tracker.json`**

```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Implementation Tracker — registrar progreso",
      "trigger": "PostToolUse",
      "matcher": "fs_write|str_replace|fs_append",
      "action": {
        "type": "agent",
        "prompt": "Si hay un plan activo en .kiro/implementation-log.json con tareas 'in_progress' o 'pending', actualiza el tracker:\n1. Si es la primera escritura de una tarea pendiente: marca started_at con timestamp actual.\n2. Si la escritura completa una tarea del plan: marca completed_at, registra files_modified y lines_added/removed.\n3. Recalcula metrics del plan.\n\nSi no hay plan activo, no hagas nada. No preguntes al usuario — el tracking es silencioso."
      }
    }
  ]
}
```

**Agregar a la lista de hooks en los generadores:**

```python
hook_files = [
    "pre-write-gate",
    "responsible-use",
    "code-review-gate",
    "test-coverage-gate",
    "build-validate",
    "integrity-check",
    "summary-on-completion",
    "implementation-tracker",  # NUEVO
]
```

---

### TASK E5 — Actualizar hook summary-on-completion para incluir estado del tracker

El hook `summary-on-completion.json` debe, además de resumir cambios, reportar el estado del plan activo:

```
Al finalizar sesión:
1. Resumen de archivos creados/modificados
2. Si hay plan activo en .kiro/implementation-log.json:
   - Mostrar progreso: "Plan X: 3/5 tareas completadas"
   - Listar tareas pendientes
   - Informar tiempo total de la sesión
3. Sugerir ejecutar Trash Inspector si hubo cambios significativos
4. Pedir validación final
```

---

## ORDEN DE EJECUCIÓN ACTUALIZADO

```
A1-A7          (infraestructura compartida)
E1-E5          (implementation tracker — transversal, puede ir en paralelo con B/C)
B1-B3          (Node completo)
C1-C3          (Python completo)
D1-D2          (verificación)
```

El bloque E es transversal y puede implementarse junto con A (antes de B y C) para que los 3 stacks ya nazcan con el tracker.
