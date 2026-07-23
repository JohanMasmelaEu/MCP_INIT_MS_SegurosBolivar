"""Tool: get_required_inputs — schema de datos requeridos para generar un proyecto."""

# Stacks soportados por el MCP
_SUPPORTED_STACKS = {"java-spring-boot", "node-express", "python-fastapi"}


def handle_get_required_inputs(stack: str) -> dict:
    """Retorna el schema de inputs agrupado por categorias para el stack indicado.

    Args:
        stack: Identificador del stack tecnologico.

    Returns:
        Schema JSON con categorias, campos, tipos, defaults y ejemplos.
    """
    if stack not in _SUPPORTED_STACKS:
        available = ", ".join(sorted(_SUPPORTED_STACKS))
        return {
            "error": f"Stack '{stack}' no soportado. Stacks disponibles: {available}",
        }

    categories = _common_categories()

    # Agregar categoria especifica del stack
    if stack == "node-express":
        categories.append(_node_specific_category())
    elif stack == "python-fastapi":
        categories.append(_python_specific_category())

    return {
        "stack": stack,
        "categories": categories,
    }


def _common_categories() -> list[dict]:
    """Categorias comunes a todos los stacks."""
    return [
        _project_identity_category(),
        _domain_modules_category(),
        _database_category(),
        _authentication_category(),
        _security_details_category(),
        _integrations_category(),
        _observability_category(),
        _ports_category(),
        _localstack_category(),
        _artifactory_category(),
        _mcp_marketplace_category(),
        _project_metadata_category(),
    ]


def _node_specific_category() -> dict:
    """Categoria especifica para Node.js/Express."""
    return {
        "name": "node_specific",
        "label": "Configuracion Node.js",
        "fields": [
            {
                "key": "typescript_strict",
                "label": "TypeScript strict mode",
                "type": "boolean",
                "default": True,
                "description": (
                    "strict:true en tsconfig. Default recomendado. "
                    "Desactivar solo si hay razon tecnica justificada."
                ),
            },
            {
                "key": "use_husky",
                "label": "Incluir Husky + lint-staged (pre-commit hooks)",
                "type": "boolean",
                "default": True,
                "description": (
                    "Si se habilita: ESLint + Prettier corren automaticamente en cada commit "
                    "sobre los archivos staged. Previene que codigo con errores de lint llegue al PR. "
                    "Si se deshabilita: el linting solo ocurre en CI (pipeline) o manualmente. "
                    "Codigo con errores podria llegar al PR y ser rechazado alli."
                ),
            },
            {
                "key": "npm_scope",
                "label": "Scope npm (ej: @bolivar)",
                "type": "string",
                "required": False,
                "default": None,
                "description": (
                    "Si se indica, el package.json usa ese scope. Si no, queda sin scope."
                ),
            },
            {
                "key": "use_npmrc",
                "label": "Generar .npmrc con registry Artifactory",
                "type": "boolean",
                "default": False,
                "description": (
                    "Genera .npmrc apuntando a Artifactory institucional. "
                    "Activar si el proyecto usa dependencias privadas @bolivar."
                ),
            },
        ],
    }


def _python_specific_category() -> dict:
    """Categoria especifica para Python/FastAPI."""
    return {
        "name": "python_specific",
        "label": "Configuracion Python",
        "fields": [
            {
                "key": "mypy_strict",
                "label": "mypy strict mode",
                "type": "boolean",
                "default": True,
                "description": (
                    "mypy --strict en config. Default recomendado. "
                    "Desactivar solo si hay razon tecnica justificada."
                ),
            },
            {
                "key": "use_pre_commit",
                "label": "Incluir pre-commit hooks (ruff + mypy en staged files)",
                "type": "boolean",
                "default": True,
                "description": (
                    "Si se habilita: ruff + mypy corren automaticamente en cada commit "
                    "sobre los archivos staged. Previene que codigo con errores llegue al PR. "
                    "Si se deshabilita: lint y type-check solo ocurren en CI o manualmente."
                ),
            },
        ],
    }


def _project_identity_category() -> dict:
    """Categoria: identidad del proyecto."""
    return {
        "name": "project_identity",
        "label": "Identidad del Proyecto",
        "fields": [
            {
                "key": "project_name",
                "label": "Nombre del microservicio",
                "type": "string",
                "required": True,
                "pattern": "^[a-z][a-z0-9-]+-ms$",
                "example": "gestion-polizas-ms",
                "description": "Nombre en kebab-case terminado en -ms",
            },
            {
                "key": "group_id",
                "label": "Grupo Gradle/Maven (solo Java)",
                "type": "string",
                "required": False,
                "default": "com.bolivar.comunes",
                "example": "com.bolivar.comunes",
                "description": "Aplica solo para stack java-spring-boot.",
            },
            {
                "key": "context_path",
                "label": "Context-path / base path del API",
                "type": "string",
                "required": True,
                "pattern": "^/[a-z_][a-z0-9_]*$",
                "example": "/gestion_polizas",
                "description": "Path base del API. Sin /api (los controllers/routers lo agregan)",
            },
            {
                "key": "api_description",
                "label": "Descripcion del API",
                "type": "string",
                "required": True,
                "example": "API del dominio Gestion de Polizas",
            },
            {
                "key": "api_version",
                "label": "Version del API",
                "type": "string",
                "required": False,
                "default": "1.0.0",
            },
        ],
    }


def _domain_modules_category() -> dict:
    """Categoria: modulos de dominio."""
    return {
        "name": "domain_modules",
        "label": "Modulos de Dominio (entidades y CRUDs)",
        "description": (
            "Cada modulo genera un CRUD REST completo: controller/router, DTOs/schemas, "
            "service, repository, model/entity y tests."
        ),
        "fields": [
            {
                "key": "modules",
                "label": "Lista de modulos",
                "type": "array",
                "required": True,
                "min_items": 1,
                "item_schema": {
                    "module_name": {
                        "type": "string",
                        "description": "Nombre del modulo lowercase (ej: polizas)",
                        "pattern": "^[a-z][a-z0-9]*$",
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Nombre de la entidad PascalCase (ej: Poliza)",
                        "pattern": "^[A-Z][a-zA-Z0-9]*$",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Nombre de la tabla UPPER_CASE (ej: POLIZA)",
                        "pattern": "^[A-Z][A-Z0-9_]*$",
                    },
                    "resource_path": {
                        "type": "string",
                        "description": "Path REST (opcional, default = module_name)",
                        "required": False,
                    },
                    "has_cod_field": {
                        "type": "boolean",
                        "description": "Si tiene campo cod_<entidad> autogenerado",
                        "default": True,
                    },
                    "fields": {
                        "type": "array",
                        "description": "Campos de la entidad (sin id, cod, ni auditoria)",
                        "item_schema": {
                            "name": "string (camelCase)",
                            "field_type": "String|Long|Integer|Boolean|BigDecimal|LocalDate|LocalDateTime|UUID",
                            "column_name": "string (snake_case)",
                            "nullable": "boolean (default: true)",
                            "length": "integer (solo para String, opcional)",
                            "unique": "boolean (default: false)",
                            "description": "string (para OpenAPI, opcional)",
                        },
                    },
                },
                "example": [
                    {
                        "module_name": "polizas",
                        "entity_name": "Poliza",
                        "table_name": "POLIZA",
                        "has_cod_field": True,
                        "fields": [
                            {"name": "nombre", "field_type": "String", "column_name": "nombre", "nullable": False, "length": 255},
                            {"name": "estado", "field_type": "Boolean", "column_name": "estado", "nullable": False},
                            {"name": "fechaEmision", "field_type": "LocalDate", "column_name": "fecha_emision", "nullable": True},
                            {"name": "montoCobertura", "field_type": "BigDecimal", "column_name": "monto_cobertura", "nullable": True},
                        ],
                    }
                ],
            },
        ],
    }


def _database_category() -> dict:
    """Categoria: base de datos."""
    return {
        "name": "database",
        "label": "Base de Datos (PostgreSQL)",
        "fields": [
            {
                "key": "db_name",
                "label": "Nombre de la BD PostgreSQL",
                "type": "string",
                "required": True,
                "example": "gestion_polizas_db",
            },
            {
                "key": "db_schema",
                "label": "Schema PostgreSQL",
                "type": "string",
                "required": False,
                "default": "public",
                "example": "gestion_polizas",
            },
            {
                "key": "db_user",
                "label": "Usuario BD (local)",
                "type": "string",
                "required": True,
                "example": "gestion_polizas_user",
            },
            {
                "key": "db_password",
                "label": "Contrasena BD (local)",
                "type": "string",
                "required": True,
                "example": "gestion_polizas_pass",
            },
            {
                "key": "db_port",
                "label": "Puerto PostgreSQL local",
                "type": "integer",
                "required": False,
                "default": 5433,
            },
            {
                "key": "ssm_prefix",
                "label": "Prefijo SSM para parametros BD (si ya existe en AWS)",
                "type": "string",
                "required": False,
                "description": "Si no se indica, se genera automaticamente desde el nombre del proyecto",
                "example": "/gestionpolizas/dev",
            },
        ],
    }


def _authentication_category() -> dict:
    """Categoria: autenticacion."""
    return {
        "name": "authentication",
        "label": "Autenticacion",
        "fields": [
            {
                "key": "auth_strategy",
                "label": "Estrategia de autenticacion",
                "type": "enum",
                "required": True,
                "options": [
                    {"value": "oauth2-resource-server", "description": "JWT validado localmente (OAuth2 Resource Server)"},
                    {"value": "api-gateway-delegated", "description": "Confia en API Gateway (sin validacion local de JWT)"},
                    {"value": "machine-to-machine", "description": "Client credentials entre servicios"},
                    {"value": "deferred", "description": "Placeholder — se define despues (genera estructura preparada)"},
                ],
                "default": "deferred",
                "description": (
                    "Seleccionar 'deferred' si aun no se tiene definida la estrategia de auth. "
                    "Se genera SecurityConfig con TODO markers listo para enchufar cualquier esquema."
                ),
            },
        ],
    }


def _integrations_category() -> dict:
    """Categoria: integraciones."""
    return {
        "name": "integrations",
        "label": "Integraciones",
        "fields": [
            {
                "key": "uses_s3",
                "label": "Requiere AWS S3 (archivos, presigned URLs)",
                "type": "boolean",
                "default": False,
            },
            {
                "key": "uses_sqs",
                "label": "Requiere AWS SQS (colas de mensajes)",
                "type": "boolean",
                "default": False,
            },
            {
                "key": "uses_soap",
                "label": "Requiere integraciones SOAP/WS (sistemas legacy)",
                "type": "boolean",
                "default": False,
            },
            {
                "key": "external_http_services",
                "label": "Servicios HTTP externos a consumir",
                "type": "array",
                "required": False,
                "item_schema": {
                    "name": "string (camelCase, ej: repositorioDocumental)",
                    "base_url_env_var": "string (ej: APP_REPOSITORIO_DOCUMENTAL_BASE_URL)",
                    "description": "string",
                    "requires_oauth": "boolean (default: false)",
                },
            },
        ],
    }


def _observability_category() -> dict:
    """Categoria: observabilidad."""
    return {
        "name": "observability",
        "label": "Observabilidad (Datadog Agent local)",
        "description": (
            "Datadog Agent en modo no-forward: valida instrumentacion sin enviar a la nube. "
            "Cero costos, cero dependencia de API key real."
        ),
        "fields": [
            {
                "key": "datadog_enabled",
                "label": "Incluir Datadog Agent local (sin forward a cloud)",
                "type": "boolean",
                "default": True,
            },
            {
                "key": "dd_service_name",
                "label": "Nombre del servicio en Datadog",
                "type": "string",
                "required": False,
                "description": "Si no se indica, se usa el nombre del microservicio",
            },
        ],
    }


def _artifactory_category() -> dict:
    """Categoria: artifactory."""
    return {
        "name": "artifactory",
        "label": "JFrog Artifactory",
        "fields": [
            {
                "key": "artifactory_url",
                "label": "URL base de JFrog Artifactory",
                "type": "string",
                "default": "https://segurosbolivar.jfrog.io/artifactory",
                "description": "URL institucional. No cambiar a menos que sea un entorno diferente.",
            },
        ],
    }


def _mcp_marketplace_category() -> dict:
    """Categoria: MCP Marketplace — seleccion de MCP servers para el proyecto."""
    return {
        "name": "mcp_marketplace",
        "label": "MCP Marketplace (Servidores de Kiro)",
        "description": (
            "Selecciona los MCP Servers que deseas tener pre-configurados en el proyecto generado. "
            "Cada MCP agrega capacidades especificas a Kiro dentro del contexto del proyecto. "
            "El proyecto generado incluira .kiro/settings/mcp.json con los seleccionados listos para usar."
        ),
        "fields": [
            {
                "key": "selected_mcps",
                "label": "MCP Servers a incluir",
                "type": "array",
                "required": False,
                "description": "Lista de IDs de MCPs seleccionados del catalogo. Si no se indica, se incluye MCP_INIT por defecto.",
                "catalog": [
                    {
                        "id": "MCP_INIT_MS_SegurosBolivar",
                        "name": "MCP Inicializador de Microservicios",
                        "auto_include": True,
                        "description": (
                            "Permite extender el proyecto desde Kiro: agregar modulos de dominio (CRUD completo), "
                            "reconfigurar infraestructura (docker-compose, SSM, .env), consultar el blueprint "
                            "tecnico del stack y ver el arquetipo visual del proyecto en localhost:9752."
                        ),
                        "capabilities": [
                            "add_domain_module: Agrega entidades CRUD completas sin salir del chat",
                            "configure_infrastructure: Modifica docker-compose, SSM params y variables",
                            "get_blueprint: Consulta el blueprint tecnico como contexto para Kiro",
                            "set_output_directory: Configura donde se generan nuevos proyectos",
                        ],
                        "docker_args": [
                            "run", "-i", "--rm",
                            "--pull", "always",
                            "-v", "C:/REPOS:/repos",
                            "-v", "mcp-init-settings:/settings",
                            "-p", "9752:9752",
                            "ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest",
                        ],
                    },
                    {
                        "id": "MCP_HU_SegurosBolivar",
                        "name": "MCP Historias de Usuario",
                        "auto_include": False,
                        "description": (
                            "Panel de 10 expertos para analisis de Historias de Usuario. Detecta gaps, "
                            "ambiguedades y contradicciones. Memoria contextual que aprende del proyecto. "
                            "Estimacion adaptativa con calibracion por velocidad real del equipo. "
                            "Visibilidad transversal entre apps del ecosistema. Grafo visual en localhost:9751."
                        ),
                        "capabilities": [
                            "analyze_story: Analiza una HU con 10 expertos (negocio, UX, backend, seguridad, etc.)",
                            "detect_conflicts: Encuentra duplicaciones y contradicciones entre HUs",
                            "estimate_story: Estima esfuerzo optimista/probable/pesimista con confianza",
                            "suggest_next_stories: Sugiere HUs faltantes basado en flujos incompletos",
                            "get_cross_app_context: Contexto transversal desde otras apps del ecosistema",
                        ],
                        "docker_args": [
                            "run", "-i", "--rm",
                            "--pull", "always",
                            "-v", "mcp-hu-memory:/workspace",
                            "-p", "9751:9751",
                            "ghcr.io/johanmasmelaeu/mcp-hu-segurosbolivar:latest",
                        ],
                    },
                ],
            },
        ],
    }


def _ports_category() -> dict:
    """Categoria: puertos locales para evitar colisiones."""
    return {
        "name": "ports",
        "label": "Puertos Locales",
        "description": (
            "Puertos para evitar colisiones si hay otros MS corriendo en la misma maquina. "
            "Si no se cambian, se usan los defaults. "
            "Defaults: Java=8080, Node=3000, Python=8000."
        ),
        "fields": [
            {
                "key": "app_port",
                "label": "Puerto HTTP de la app",
                "type": "integer",
                "required": False,
                "default": 8080,
                "description": "Default segun stack: Java=8080, Node=3000, Python=8000. Cambiar si hay colision.",
            },
            {
                "key": "localstack_port",
                "label": "Puerto de LocalStack",
                "type": "integer",
                "required": False,
                "default": 4566,
                "description": "Cambiar si otro MS ya usa 4566 (ej: 4567, 4568).",
            },
            {
                "key": "redis_port",
                "label": "Puerto Redis local (solo si cache=redis)",
                "type": "integer",
                "required": False,
                "default": 6379,
                "description": "Cambiar si otro servicio ya usa 6379 (ej: 6380).",
            },
        ],
    }


def _localstack_category() -> dict:
    """Categoria: servicios AWS simulados en LocalStack."""
    return {
        "name": "localstack",
        "label": "Servicios AWS Simulados (LocalStack)",
        "description": "Servicios de AWS que LocalStack simulara en el ambiente local.",
        "fields": [
            {
                "key": "localstack_services",
                "label": "Servicios a habilitar",
                "type": "array",
                "required": False,
                "default": ["ssm"],
                "description": "Servicios AWS que LocalStack simulara en docker-compose.",
                "options": ["ssm", "secretsmanager", "s3", "sqs", "events"],
                "example": ["ssm", "secretsmanager"],
            },
        ],
    }


def _security_details_category() -> dict:
    """Categoria: detalles adicionales de seguridad."""
    return {
        "name": "security_details",
        "label": "Configuracion de Seguridad (detalles)",
        "description": "Detalles adicionales de seguridad que dependen de la auth_strategy elegida.",
        "fields": [
            {
                "key": "cors_allow_credentials",
                "label": "CORS allowCredentials",
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "False para APIs M2M sin cookies. True si hay frontend con sesion.",
            },
            {
                "key": "extra_public_paths",
                "label": "Endpoints publicos adicionales (sin auth)",
                "type": "array",
                "required": False,
                "default": [],
                "description": "Paths que no requieren token (ej: /api/v1/auth/token, /api/v1/health).",
                "example": ["/api/v1/auth/token", "/api/v1/conexion/**"],
            },
            {
                "key": "openapi_base_path",
                "label": "Path base OpenAPI/Swagger",
                "type": "string",
                "required": False,
                "default": None,
                "description": "Path custom para la documentacion. Si no se indica, se genera automaticamente (ej: /srv-miapp-openapi).",
                "example": "/srv-cucoperacional-openapi",
            },
        ],
    }


def _project_metadata_category() -> dict:
    """Categoria: metadatos adicionales del proyecto."""
    return {
        "name": "project_metadata",
        "label": "Metadatos del Proyecto",
        "description": "Configuracion adicional para i18n, cache y contenedorizacion.",
        "fields": [
            {
                "key": "i18n",
                "label": "Idiomas activos para mensajes",
                "type": "array",
                "required": False,
                "default": ["es"],
                "example": ["es", "en"],
                "description": "Idiomas para mensajes de error/validacion. Default: solo espanol.",
            },
            {
                "key": "cache",
                "label": "Tecnologia de cache (opcional)",
                "type": "string",
                "required": False,
                "default": None,
                "options": [
                    {"value": "redis", "description": "Redis como cache distribuido"},
                    {"value": None, "description": "Sin cache"},
                ],
            },
            {
                "key": "docker_profile",
                "label": "Perfil de imagen Docker",
                "type": "string",
                "required": False,
                "default": None,
                "description": "Define que incluye la imagen Docker. Se indexa en project.json.",
                "example": "java-redis",
            },
        ],
    }
