"""Tool: get_project_plan — genera el plan detallado de archivos sin ejecutar."""

from src.models.project_config import AuthStrategy, ProjectConfig

# Mapeo de stack a funcion constructora de file tree
_FILE_TREE_BUILDERS = {}


def handle_get_project_plan(config_dict: dict) -> dict:
    """Genera el plan de archivos y carpetas a crear.

    Valida la configuracion con Pydantic y construye el arbol de archivos
    que se generaria, sin escribir nada en disco.

    Args:
        config_dict: Configuracion del proyecto como diccionario.

    Returns:
        Plan detallado con arbol de archivos, decisiones y next steps.
    """
    try:
        config = ProjectConfig(**config_dict)
    except Exception as e:
        return {"error": f"Configuracion invalida: {e}"}

    files = _build_file_tree(config)
    decisions = _build_decisions(config)
    next_steps = _build_next_steps(config)

    return {
        "project_name": config.project_name,
        "stack": config.stack,
        "target_directory": config.project_name,
        "total_files": len(files),
        "total_directories": len(set(f["path"].rsplit("/", 1)[0] for f in files if "/" in f["path"])),
        "tree": files,
        "decisions_made": decisions,
        "next_steps_after_generation": next_steps,
    }


def _build_file_tree(config: ProjectConfig) -> list[dict]:
    """Construye la lista de archivos que se generarian, delegando al stack."""
    stack = config.stack
    if stack == "java-spring-boot":
        return _build_java_file_tree(config)
    elif stack == "node-express":
        return _build_node_file_tree(config)
    elif stack == "python-fastapi":
        return _build_python_file_tree(config)
    else:
        return [_file("ERROR", f"Stack '{stack}' no tiene file tree definido.")]


def _build_java_file_tree(config: ProjectConfig) -> list[dict]:
    """Construye la lista de archivos para el stack Java/Spring Boot."""
    p = config.project_name
    pkg = config.base_package_path
    files = []

    # --- Gradle ---
    files.extend([
        _file(f"{p}/build.gradle", "Gradle build: Spring Boot 4.0.2, Java 21, dependencias, JaCoCo"),
        _file(f"{p}/settings.gradle", f"rootProject.name = '{config.artifact_name}'"),
        _file(f"{p}/gradlew", "Gradle wrapper script (Unix)"),
        _file(f"{p}/gradlew.bat", "Gradle wrapper script (Windows)"),
        _file(f"{p}/gradle/wrapper/gradle-wrapper.properties", "Gradle 9.4.1 distribution URL"),
        _file(f"{p}/gradle/wrapper/gradle-wrapper.jar", "Gradle wrapper JAR (binario)"),
    ])

    # --- Git ---
    files.extend([
        _file(f"{p}/.gitignore", "Exclusiones: .idea, build, node_modules, __pycache__, .env"),
        _file(f"{p}/.gitattributes", "Normalizacion de line endings"),
    ])

    # --- Fuentes Java: base ---
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/{config.application_class_name}.java", "Main class @SpringBootApplication"),
        _file(f"{p}/src/main/java/{pkg}/{config.configuration_class_name}.java", "Configuracion raiz"),
    ])

    # --- commons/ ---
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/commons/ApiResponseDTO.java", "Interface contrato respuesta API"),
        _file(f"{p}/src/main/java/{pkg}/commons/ApiResponseData.java", "Implementacion con sanitizacion XSS"),
        _file(f"{p}/src/main/java/{pkg}/commons/ApiResponseMensajes.java", "Constantes mensajes HTTP"),
        _file(f"{p}/src/main/java/{pkg}/commons/UsuarioAuditoriaProvider.java", "Extrae usuario del token para auditoria"),
    ])

    # --- config/ ---
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/config/DataBaseConfiguration.java", "DataSource dinamico via SSM"),
        _file(f"{p}/src/main/java/{pkg}/config/ParameterStoreClient.java", "Interface contrato SSM"),
        _file(f"{p}/src/main/java/{pkg}/config/SsmParameterStoreConfiguration.java", "Implementacion SDK AWS SSM"),
        _file(f"{p}/src/main/java/{pkg}/config/OpenApiConfiguration.java", "SpringDoc: metadata + servers dinamicos"),
        _file(f"{p}/src/main/java/{pkg}/config/WebClientConfiguration.java", "WebClient para HTTP saliente"),
        _file(f"{p}/src/main/java/{pkg}/config/HtmlEntitiesJacksonConfiguration.java", "Jackson config sanitizacion"),
        _file(f"{p}/src/main/java/{pkg}/config/JsonUtf8Configuration.java", "Forzar UTF-8 en responses"),
    ])

    # --- config/security/ ---
    auth_desc = _auth_description(config.auth_strategy)
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/config/security/SecurityConfig.java", f"Spring Security: {auth_desc}"),
        _file(f"{p}/src/main/java/{pkg}/config/security/SecurityHeadersFilter.java", "Headers: HSTS, X-Content-Type-Options, X-Frame-Options"),
        _file(f"{p}/src/main/java/{pkg}/config/security/ApiErrorAccessDeniedHandler.java", "Handler 403 con formato API estandar"),
        _file(f"{p}/src/main/java/{pkg}/config/security/ApiErrorAuthenticationEntryPoint.java", "Handler 401 con formato API estandar"),
    ])

    # --- entity/ ---
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/entity/AuditoriaCompleta.java", "MappedSuperclass: creacion + actualizacion"),
        _file(f"{p}/src/main/java/{pkg}/entity/AuditoriaSoloCreacion.java", "MappedSuperclass: solo creacion"),
    ])

    # --- errorhandling/ ---
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/errorhandling/BolivarBusinessException.java", "Excepcion de negocio con builder"),
        _file(f"{p}/src/main/java/{pkg}/errorhandling/GlobalExceptionHandler.java", "@ControllerAdvice centralizado"),
        _file(f"{p}/src/main/java/{pkg}/errorhandling/TipoErrorEnum.java", "Enum: TECNICO | NEGOCIO"),
        _file(f"{p}/src/main/java/{pkg}/errorhandling/ValidationExceptionHandler.java", "Handler para Jakarta Validation"),
    ])

    # --- utils/ ---
    files.extend([
        _file(f"{p}/src/main/java/{pkg}/utils/DataSanitizer.java", "Sanitizacion XSS de payloads"),
        _file(f"{p}/src/main/java/{pkg}/utils/HtmlEntityEncoder.java", "Encoder HTML entities"),
    ])

    # --- Modulos de dominio ---
    for module in config.modules:
        mod_path = f"{p}/src/main/java/{pkg}/{module.module_name}"
        test_path = f"{p}/src/test/java/{pkg}/{module.module_name}"
        files.extend([
            _file(f"{mod_path}/controller/{module.entity_name}Controller.java", f"CRUD REST para {module.entity_name}"),
            _file(f"{mod_path}/dto/{module.entity_name}CrearRequestDTO.java", "DTO creacion con Jakarta Validation"),
            _file(f"{mod_path}/dto/{module.entity_name}ActualizarRequestDTO.java", "DTO actualizacion"),
            _file(f"{mod_path}/dto/{module.entity_name}FiltrosRequestDTO.java", "DTO filtros paginados"),
            _file(f"{mod_path}/dto/{module.entity_name}ResponseDTO.java", "DTO respuesta"),
            _file(f"{mod_path}/services/{module.entity_name}Service.java", "Interface servicio"),
            _file(f"{mod_path}/services/{module.entity_name}ServiceImpl.java", "Implementacion servicio"),
            _file(f"{mod_path}/repository/{module.entity_name}Repository.java", "JpaRepository + JpaSpecificationExecutor"),
            _file(f"{mod_path}/repository/{module.entity_name}Specification.java", "Criteria API filtros dinamicos"),
            _file(f"{p}/src/main/java/{pkg}/entity/{module.entity_name}.java", f"Entidad JPA tabla {module.table_name}"),
            _file(f"{test_path}/controller/{module.entity_name}ControllerTest.java", "Test de integracion MockMvc"),
            _file(f"{test_path}/services/{module.entity_name}ServiceTest.java", "Test unitario con Mockito"),
        ])

    # --- Resources ---
    files.extend([
        _file(f"{p}/src/main/resources/application.yaml", "Configuracion principal Spring"),
        _file(f"{p}/src/main/resources/application-local.yaml", "Perfil local: CORS abierto, mock OAuth"),
        _file(f"{p}/src/main/resources/application-test.yaml", "Perfil test: H2, sin SSM"),
    ])

    # --- Test base ---
    files.extend([
        _file(f"{p}/src/test/java/{pkg}/{config.application_class_name}Test.java", "Test de carga de contexto"),
    ])

    # --- Infraestructura ---
    files.extend([
        _file(f"{p}/development/docker-local-ms/Dockerfile", "Multi-stage: JDK 21 build + JRE 21 runtime + dd-java-agent"),
        _file(f"{p}/development/docker-local-ms/docker-compose.yml", "LocalStack + Mock OAuth + DD Agent + App"),
        _file(f"{p}/development/docker-local-ms/down.ps1", "Script para detener compose (Windows)"),
        _file(f"{p}/development/docker-local-ms/down.sh", "Script para detener compose (Unix)"),
        _file(f"{p}/development/docker-local-ms/scripts/seed-localstack-ssm.sh", "Semilla parametros SSM en LocalStack"),
        _file(f"{p}/development/.env.sample", "Template de variables de entorno"),
    ])

    # Mock OAuth solo si aplica
    if config.auth_strategy.value == "oauth2-resource-server":
        files.append(
            _file(f"{p}/development/docker-local-ms/config/mock-oauth-config.json", "Config Mock OAuth Server")
        )

    # --- CI/CD ---
    files.extend([
        _file(f"{p}/.github/workflows/pipeline.yaml", "CI/CD push: template institucional Gradle 21"),
        _file(f"{p}/.github/workflows/pull-request.yml", "PR analysis: template institucional"),
        _file(f"{p}/.github/CODEOWNERS", "Code owners del repositorio"),
        _file(f"{p}/.github/pull_request_template.md", "Template de PR"),
    ])

    # --- Documentacion ---
    files.extend([
        _file(f"{p}/README.md", "README del proyecto con instrucciones completas"),
        _file(f"{p}/api_spec.yaml", "OpenAPI 3.x spec base"),
        _file(f"{p}/.env", "Variables de entorno locales (gitignored)"),
    ])

    # --- Kiro context ---
    files.extend([
        _file(f"{p}/.kiro/project.json", "Metadato del proyecto: stack, cache, i18n, dockerProfile"),
        _file(f"{p}/.kiro/steering/00-org-conventions.md", "Convenciones organizacionales: URLs, naming, idioma, docs"),
        _file(f"{p}/.kiro/steering/01-architecture.md", "Arquitectura backend: dominios, contratos, resiliencia"),
        _file(f"{p}/.kiro/steering/02-security.md", "Seguridad: Zero Trust, inyeccion, headers, secrets"),
        _file(f"{p}/.kiro/steering/03-code-style.md", "Codigo limpio: SOLID, funciones, Trash Inspector"),
        _file(f"{p}/.kiro/steering/04-testing-standards.md", "Testing: 80% coverage, Given/When/Then"),
        _file(f"{p}/.kiro/steering/05-responsible-ai-use.md", "Uso responsable IA: plan obligatorio, adherencia arquitectura"),
        _file(f"{p}/.kiro/steering/06-data-access.md", "Acceso datos: ORM obligatorio, no raw SQL"),
        _file(f"{p}/.kiro/steering/07-error-handling.md", "Excepciones: cero 500, captura obligatoria"),
        _file(f"{p}/.kiro/steering/08-observability.md", "Observabilidad: logs por ambiente, masking, correlation-id"),
        _file(f"{p}/.kiro/steering/10-stack-java.md", "Stack Java: JDK 21, Spring Boot 4, Gradle 9"),
        _file(f"{p}/.kiro/hooks/pre-write-gate.json", "Gate pre-escritura: plan + arquitectura + calidad"),
        _file(f"{p}/.kiro/hooks/responsible-use.json", "Validacion prompt: accion + objeto"),
        _file(f"{p}/.kiro/hooks/code-review-gate.json", "Review post-escritura: naming, tests, consistencia"),
        _file(f"{p}/.kiro/hooks/test-coverage-gate.json", "Verificacion tests al completar tarea"),
        _file(f"{p}/.kiro/hooks/build-validate.json", "Compilar al guardar .java"),
        _file(f"{p}/.kiro/hooks/integrity-check.json", "Verificar hooks activos al iniciar sesion"),
        _file(f"{p}/.kiro/hooks/summary-on-completion.json", "Resumen de cambios al finalizar sesion"),
        _file(f"{p}/.kiro/changelogs/changelog-develop.md", "Changelog inicial"),
    ])

    # --- Integraciones opcionales ---
    if config.integrations.uses_s3:
        files.extend([
            _file(f"{p}/src/main/java/{pkg}/config/S3Configuration.java", "Config AWS S3 + presigned URLs"),
            _file(f"{p}/src/main/java/{pkg}/config/S3Properties.java", "Properties S3 (bucket, region, expiration)"),
        ])

    if config.integrations.uses_sqs:
        files.extend([
            _file(f"{p}/src/main/java/{pkg}/config/SqsConfiguration.java", "Config AWS SQS + Extended Client"),
        ])

    if config.integrations.uses_soap:
        files.extend([
            _file(f"{p}/src/main/java/{pkg}/config/WsSecurityConfiguration.java", "Spring WS + WS-Security config"),
        ])

    return files


def _build_node_file_tree(config: ProjectConfig) -> list[dict]:
    """Construye la lista de archivos para el stack Node/Express/TypeScript."""
    p = config.project_name
    files = []

    # --- Root config files ---
    files.extend([
        _file(f"{p}/package.json", "Package.json con dependencias condicionales por auth/cache"),
        _file(f"{p}/tsconfig.json", f"TypeScript config (strict={config.typescript_strict})"),
        _file(f"{p}/vitest.config.ts", "Vitest config con coverage v8"),
        _file(f"{p}/eslint.config.mjs", "ESLint v9 flat config"),
        _file(f"{p}/.prettierrc", "Prettier config"),
    ])

    # --- Condicionales root ---
    if config.use_npmrc:
        files.append(_file(f"{p}/.npmrc", "Registry Artifactory institucional"))
    if config.use_husky:
        files.append(_file(f"{p}/.husky/pre-commit", "Husky pre-commit: lint-staged"))

    # --- Git ---
    files.extend([
        _file(f"{p}/.gitignore", "Exclusiones: node_modules, dist, .env, coverage"),
        _file(f"{p}/.gitattributes", "Normalizacion de line endings"),
    ])

    # --- src/ base ---
    files.extend([
        _file(f"{p}/src/app.ts", "Express app config con middlewares condicionales"),
        _file(f"{p}/src/server.ts", "Entry point: listen + graceful shutdown"),
    ])

    # --- src/config/ ---
    files.extend([
        _file(f"{p}/src/config/index.ts", "Zod schema para env vars + config export"),
        _file(f"{p}/src/config/database.ts", "Pool pg + Drizzle client"),
        _file(f"{p}/src/config/logger.ts", "Pino instance con correlation-id"),
        _file(f"{p}/src/config/security.ts", "Passport strategies condicionales por auth_strategy"),
    ])

    # --- src/commons/ ---
    files.extend([
        _file(f"{p}/src/commons/api-response.dto.ts", "Interface respuesta API estandar {codigo, mensaje, data}"),
        _file(f"{p}/src/commons/pagination.dto.ts", "DTO paginacion {content, page, size, totalPages, totalElements}"),
        _file(f"{p}/src/commons/audit.mixin.ts", "Mixin auditoria: creadoPor, fechaCreacion, etc."),
    ])

    # --- src/middleware/ ---
    files.extend([
        _file(f"{p}/src/middleware/error-handler.ts", "Error handler centralizado"),
        _file(f"{p}/src/middleware/correlation-id.ts", "Middleware correlation-id con AsyncLocalStorage"),
        _file(f"{p}/src/middleware/request-logger.ts", "Logger de requests con Pino"),
        _file(f"{p}/src/middleware/validate.ts", "Middleware validacion Zod"),
        _file(f"{p}/src/middleware/auth.ts", "Middleware auth condicional por auth_strategy"),
    ])

    # --- src/errors/ ---
    files.extend([
        _file(f"{p}/src/errors/bolivar-business.error.ts", "Error de negocio con codigo y tipo"),
        _file(f"{p}/src/errors/error-types.enum.ts", "Enum: TECNICO | NEGOCIO"),
    ])

    # --- src/utils/ ---
    files.extend([
        _file(f"{p}/src/utils/data-sanitizer.ts", "Sanitizacion XSS de payloads"),
        _file(f"{p}/src/utils/date.utils.ts", "Utilidades de fecha ISO-8601"),
    ])

    # --- Modulos de dominio ---
    for module in config.modules:
        mod = module.module_name
        files.extend([
            _file(f"{p}/src/{mod}/{mod}.controller.ts", f"Router CRUD REST para {module.entity_name}"),
            _file(f"{p}/src/{mod}/{mod}.service.ts", f"Servicio de negocio para {module.entity_name}"),
            _file(f"{p}/src/{mod}/{mod}.repository.ts", f"Repository Drizzle para {module.entity_name}"),
            _file(f"{p}/src/{mod}/{mod}.schema.ts", f"Drizzle table definition para {module.table_name}"),
            _file(f"{p}/src/{mod}/dto/crear.dto.ts", "DTO creacion con Zod"),
            _file(f"{p}/src/{mod}/dto/actualizar.dto.ts", "DTO actualizacion con Zod"),
            _file(f"{p}/src/{mod}/dto/filtros.dto.ts", "DTO filtros paginados con Zod"),
            _file(f"{p}/src/{mod}/dto/response.dto.ts", "DTO respuesta"),
            _file(f"{p}/src/{mod}/tests/{mod}.service.test.ts", "Test unitario servicio con vi.mock"),
            _file(f"{p}/src/{mod}/tests/{mod}.controller.test.ts", "Test integracion con supertest"),
        ])

    # --- tests/helpers ---
    files.append(_file(f"{p}/tests/helpers/test-app.ts", "Express app sin listen (para supertest)"))

    # --- Infraestructura ---
    files.extend([
        _file(f"{p}/Dockerfile", "Multi-stage: build (npm ci + tsc) + runtime (node:22-alpine)"),
        _file(f"{p}/docker-compose.yml", "LocalStack + Redis(condicional) + DD Agent + App"),
        _file(f"{p}/scripts/seed-localstack-ssm.sh", "Semilla parametros SSM en LocalStack"),
        _file(f"{p}/.env.sample", "Template de variables de entorno"),
        _file(f"{p}/.env", "Variables de entorno locales (gitignored)"),
    ])

    if config.auth_strategy.value == "oauth2-resource-server":
        files.append(_file(f"{p}/config/mock-oauth-config.json", "Config Mock OAuth Server"))

    # --- CI/CD ---
    files.extend([
        _file(f"{p}/.github/workflows/pipeline.yaml", "CI/CD push: build + test + lint + Docker"),
        _file(f"{p}/.github/CODEOWNERS", "Code owners del repositorio"),
        _file(f"{p}/.github/pull_request_template.md", "Template de PR"),
    ])

    # --- Documentacion ---
    files.extend([
        _file(f"{p}/README.md", "README del proyecto con instrucciones completas"),
        _file(f"{p}/api_spec.yaml", "OpenAPI 3.x spec base"),
    ])

    # --- Kiro context ---
    files.extend([
        _file(f"{p}/.kiro/project.json", "Metadato del proyecto: stack, cache, i18n, dockerProfile"),
        _file(f"{p}/.kiro/steering/00-org-conventions.md", "Convenciones organizacionales"),
        _file(f"{p}/.kiro/steering/01-architecture.md", "Arquitectura backend"),
        _file(f"{p}/.kiro/steering/02-security.md", "Seguridad: Zero Trust, headers, secrets"),
        _file(f"{p}/.kiro/steering/03-code-style.md", "Codigo limpio: SOLID, funciones"),
        _file(f"{p}/.kiro/steering/04-testing-standards.md", "Testing: 80% coverage, Given/When/Then"),
        _file(f"{p}/.kiro/steering/05-responsible-ai-use.md", "Uso responsable IA"),
        _file(f"{p}/.kiro/steering/06-data-access.md", "Acceso datos: ORM obligatorio"),
        _file(f"{p}/.kiro/steering/07-error-handling.md", "Excepciones: cero 500"),
        _file(f"{p}/.kiro/steering/08-observability.md", "Observabilidad: logs, masking, correlation-id"),
        _file(f"{p}/.kiro/steering/10-stack-node.md", "Stack Node: Node.js 22, Express, TypeScript, Drizzle"),
        _file(f"{p}/.kiro/hooks/pre-write-gate.json", "Gate pre-escritura"),
        _file(f"{p}/.kiro/hooks/responsible-use.json", "Validacion prompt"),
        _file(f"{p}/.kiro/hooks/code-review-gate.json", "Review post-escritura"),
        _file(f"{p}/.kiro/hooks/test-coverage-gate.json", "Verificacion tests"),
        _file(f"{p}/.kiro/hooks/build-validate.json", "Lint al guardar (npm run lint)"),
        _file(f"{p}/.kiro/hooks/integrity-check.json", "Verificar hooks al iniciar sesion"),
        _file(f"{p}/.kiro/hooks/summary-on-completion.json", "Resumen al finalizar sesion"),
        _file(f"{p}/.kiro/changelogs/changelog-develop.md", "Changelog inicial"),
    ])

    return files


def _build_python_file_tree(config: ProjectConfig) -> list[dict]:
    """Construye la lista de archivos para el stack Python/FastAPI."""
    p = config.project_name
    files = []

    # --- Root config files ---
    files.append(_file(f"{p}/pyproject.toml", "Config: deps condicionales, ruff, mypy, pytest"))

    # --- Condicionales root ---
    if config.use_pre_commit:
        files.append(_file(f"{p}/.pre-commit-config.yaml", "Pre-commit hooks: ruff + mypy"))

    # --- Git ---
    files.append(_file(f"{p}/.gitignore", "Exclusiones: __pycache__, .venv, dist, .env, .pytest_cache"))

    # --- src/ base ---
    files.extend([
        _file(f"{p}/src/__init__.py", "Package init"),
        _file(f"{p}/src/main.py", "App factory con lifespan, include_router, middleware condicional"),
    ])

    # --- src/config/ ---
    files.extend([
        _file(f"{p}/src/config/__init__.py", "Package init"),
        _file(f"{p}/src/config/settings.py", "Pydantic Settings (env vars)"),
        _file(f"{p}/src/config/database.py", "AsyncEngine + AsyncSession factory"),
        _file(f"{p}/src/config/logging.py", "structlog config con correlation-id"),
        _file(f"{p}/src/config/security.py", "JWT decode, auth dependencies por auth_strategy"),
    ])

    # --- src/commons/ ---
    files.extend([
        _file(f"{p}/src/commons/__init__.py", "Package init"),
        _file(f"{p}/src/commons/api_response.py", "Modelo respuesta API {codigo, mensaje, data}"),
        _file(f"{p}/src/commons/pagination.py", "Modelo paginacion {content, page, size, total_pages, total_elements}"),
        _file(f"{p}/src/commons/audit_mixin.py", "Mixin SQLAlchemy: created_by, created_at, etc."),
    ])

    # --- src/middleware/ ---
    files.extend([
        _file(f"{p}/src/middleware/__init__.py", "Package init"),
        _file(f"{p}/src/middleware/correlation_id.py", "Middleware correlation-id con contextvars"),
        _file(f"{p}/src/middleware/error_handler.py", "Exception handler centralizado"),
        _file(f"{p}/src/middleware/request_logger.py", "Logger de requests con structlog"),
        _file(f"{p}/src/middleware/security_headers.py", "Middleware security headers (HSTS, X-Content-Type-Options)"),
    ])

    # --- src/errors/ ---
    files.extend([
        _file(f"{p}/src/errors/__init__.py", "Package init"),
        _file(f"{p}/src/errors/bolivar_business_error.py", "Excepcion de negocio con codigo y tipo"),
        _file(f"{p}/src/errors/error_types.py", "Enum: TECNICO | NEGOCIO"),
    ])

    # --- src/utils/ ---
    files.extend([
        _file(f"{p}/src/utils/__init__.py", "Package init"),
        _file(f"{p}/src/utils/data_sanitizer.py", "Sanitizacion XSS de payloads"),
        _file(f"{p}/src/utils/date_utils.py", "Utilidades de fecha ISO-8601"),
    ])

    # --- Modulos de dominio ---
    for module in config.modules:
        mod = module.module_name
        files.extend([
            _file(f"{p}/src/{mod}/__init__.py", "Package init"),
            _file(f"{p}/src/{mod}/router.py", f"Router CRUD REST para {module.entity_name}"),
            _file(f"{p}/src/{mod}/service.py", f"Servicio de negocio para {module.entity_name}"),
            _file(f"{p}/src/{mod}/repository.py", f"Repository SQLAlchemy async para {module.entity_name}"),
            _file(f"{p}/src/{mod}/models.py", f"SQLAlchemy model para {module.table_name}"),
            _file(f"{p}/src/{mod}/schemas/__init__.py", "Package init"),
            _file(f"{p}/src/{mod}/schemas/crear.py", "Schema Pydantic creacion"),
            _file(f"{p}/src/{mod}/schemas/actualizar.py", "Schema Pydantic actualizacion"),
            _file(f"{p}/src/{mod}/schemas/filtros.py", "Schema Pydantic filtros paginados"),
            _file(f"{p}/src/{mod}/schemas/response.py", "Schema Pydantic respuesta"),
            _file(f"{p}/src/{mod}/tests/__init__.py", "Package init"),
            _file(f"{p}/src/{mod}/tests/test_service.py", "Test unitario servicio con AsyncMock"),
            _file(f"{p}/src/{mod}/tests/test_router.py", "Test integracion con httpx"),
        ])

    # --- tests/ base ---
    files.extend([
        _file(f"{p}/tests/__init__.py", "Package init"),
        _file(f"{p}/tests/conftest.py", "Fixtures: app, client httpx, AsyncSession"),
        _file(f"{p}/tests/factories/__init__.py", "Package init factories"),
    ])

    # --- Infraestructura ---
    files.extend([
        _file(f"{p}/Dockerfile", "Multi-stage: uv build deps + python:3.12-slim runtime"),
        _file(f"{p}/docker-compose.yml", "LocalStack + Redis(condicional) + DD Agent + App"),
        _file(f"{p}/scripts/seed-localstack-ssm.sh", "Semilla parametros SSM en LocalStack"),
        _file(f"{p}/.env.sample", "Template de variables de entorno"),
        _file(f"{p}/.env", "Variables de entorno locales (gitignored)"),
    ])

    if config.auth_strategy.value == "oauth2-resource-server":
        files.append(_file(f"{p}/config/mock-oauth-config.json", "Config Mock OAuth Server"))

    # --- CI/CD ---
    files.extend([
        _file(f"{p}/.github/workflows/pipeline.yaml", "CI/CD push: ruff + mypy + pytest + Docker"),
        _file(f"{p}/.github/CODEOWNERS", "Code owners del repositorio"),
        _file(f"{p}/.github/pull_request_template.md", "Template de PR"),
    ])

    # --- Documentacion ---
    files.extend([
        _file(f"{p}/README.md", "README del proyecto con instrucciones completas"),
        _file(f"{p}/api_spec.yaml", "OpenAPI 3.x spec base"),
    ])

    # --- Kiro context ---
    files.extend([
        _file(f"{p}/.kiro/project.json", "Metadato del proyecto: stack, cache, i18n, dockerProfile"),
        _file(f"{p}/.kiro/steering/00-org-conventions.md", "Convenciones organizacionales"),
        _file(f"{p}/.kiro/steering/01-architecture.md", "Arquitectura backend"),
        _file(f"{p}/.kiro/steering/02-security.md", "Seguridad: Zero Trust, headers, secrets"),
        _file(f"{p}/.kiro/steering/03-code-style.md", "Codigo limpio: SOLID, funciones"),
        _file(f"{p}/.kiro/steering/04-testing-standards.md", "Testing: 80% coverage, Given/When/Then"),
        _file(f"{p}/.kiro/steering/05-responsible-ai-use.md", "Uso responsable IA"),
        _file(f"{p}/.kiro/steering/06-data-access.md", "Acceso datos: ORM obligatorio"),
        _file(f"{p}/.kiro/steering/07-error-handling.md", "Excepciones: cero 500"),
        _file(f"{p}/.kiro/steering/08-observability.md", "Observabilidad: logs, masking, correlation-id"),
        _file(f"{p}/.kiro/steering/10-stack-python.md", "Stack Python: Python 3.12, FastAPI, SQLAlchemy, uv"),
        _file(f"{p}/.kiro/hooks/pre-write-gate.json", "Gate pre-escritura"),
        _file(f"{p}/.kiro/hooks/responsible-use.json", "Validacion prompt"),
        _file(f"{p}/.kiro/hooks/code-review-gate.json", "Review post-escritura"),
        _file(f"{p}/.kiro/hooks/test-coverage-gate.json", "Verificacion tests"),
        _file(f"{p}/.kiro/hooks/build-validate.json", "Lint al guardar (ruff check src/)"),
        _file(f"{p}/.kiro/hooks/integrity-check.json", "Verificar hooks al iniciar sesion"),
        _file(f"{p}/.kiro/hooks/summary-on-completion.json", "Resumen al finalizar sesion"),
        _file(f"{p}/.kiro/changelogs/changelog-develop.md", "Changelog inicial"),
    ])

    return files


def _build_decisions(config: ProjectConfig) -> list[str]:
    """Lista de decisiones arquitectonicas tomadas."""
    decisions = []

    # Stack
    stack_labels = {
        "java-spring-boot": "Java 21 + Spring Boot 4.x + Gradle 9.x",
        "node-express": "Node.js 22 + Express 4.x + TypeScript 5.x",
        "python-fastapi": "Python 3.12 + FastAPI + uv",
    }
    decisions.append(f"Stack: {stack_labels.get(config.stack, config.stack)}")

    auth_labels = {
        AuthStrategy.OAUTH2_RESOURCE_SERVER: "OAuth2 Resource Server con JWT validation local",
        AuthStrategy.API_GATEWAY_DELEGATED: "API Gateway delegated (sin validacion local)",
        AuthStrategy.MACHINE_TO_MACHINE: "Machine-to-machine (client_credentials)",
        AuthStrategy.DEFERRED: "Deferred — placeholder con TODO markers",
    }
    decisions.append(f"Auth: {auth_labels[config.auth_strategy]}")

    if config.observability.datadog_enabled:
        decisions.append("Datadog: Agent local sin forward (modo validacion instrumentacion)")
    else:
        decisions.append("Datadog: Deshabilitado")

    integrations = []
    if config.integrations.uses_s3:
        integrations.append("S3")
    if config.integrations.uses_sqs:
        integrations.append("SQS")
    if config.integrations.uses_soap:
        integrations.append("SOAP/WS")
    if config.integrations.external_http_services:
        integrations.append(f"{len(config.integrations.external_http_services)} servicios HTTP externos")

    if integrations:
        decisions.append(f"Integraciones habilitadas: {', '.join(integrations)}")
    else:
        decisions.append("Integraciones: ninguna adicional")

    decisions.append(f"BD: PostgreSQL schema '{config.database.db_schema}' en puerto {config.database.db_port}")
    decisions.append(f"Modulos de dominio: {len(config.modules)} ({', '.join(m.module_name for m in config.modules)})")

    # Puertos y cache
    decisions.append(f"Puertos: app={config.app_port}, LocalStack={config.localstack_port}")
    if config.cache:
        decisions.append(f"Cache: {config.cache} (puerto {config.redis_port})")
    else:
        decisions.append("Cache: ninguno")
    decisions.append(f"LocalStack services: {', '.join(config.localstack_services)}")
    if config.extra_public_paths:
        decisions.append(f"Endpoints publicos extra: {', '.join(config.extra_public_paths)}")
    decisions.append(f"CORS allowCredentials: {config.cors_allow_credentials}")

    return decisions


def _build_next_steps(config: ProjectConfig) -> list[str]:
    """Pasos siguientes despues de la generacion, adaptados por stack."""
    stack = config.stack
    port = config.app_port

    if stack == "java-spring-boot":
        steps = [
            "1. Copiar development/.env.sample a .env y configurar ARTIFACTORY_USER / ARTIFACTORY_PASSWORD",
            f"2. Levantar infraestructura: cd {config.project_name}/development/docker-local-ms && docker compose --env-file ../../.env up -d",
            f"3. Verificar Swagger UI: http://localhost:{port}{config.context_path}/swagger-ui.html",
            f"4. Verificar health: http://localhost:{port}{config.context_path}/actuator/health",
        ]
    elif stack == "node-express":
        steps = [
            "1. Copiar .env.sample a .env y configurar variables",
            f"2. npm install",
            f"3. docker compose up -d (LocalStack + dependencias)",
            f"4. npm run dev",
            f"5. Verificar health: http://localhost:{port}{config.context_path}/api/v1/health",
            f"6. Verificar Swagger UI: http://localhost:{port}{config.context_path}/api-docs",
        ]
    elif stack == "python-fastapi":
        steps = [
            "1. Copiar .env.sample a .env y configurar variables",
            f"2. uv sync",
            f"3. docker compose up -d (LocalStack + dependencias)",
            f"4. uv run uvicorn src.main:app --reload --port {port}",
            f"5. Verificar health: http://localhost:{port}{config.context_path}/api/v1/health",
            f"6. Verificar docs: http://localhost:{port}{config.context_path}/docs",
        ]
    else:
        steps = [f"1. cd {config.project_name} && seguir instrucciones del README"]

    if config.observability.datadog_enabled:
        steps.append(f"{len(steps) + 1}. Verificar Datadog Agent: docker logs <ms>-dd-agent | grep 'Trace received'")

    if config.auth_strategy == AuthStrategy.DEFERRED:
        steps.append("PENDIENTE: Definir estrategia de auth y completar SecurityConfig (buscar TODO markers)")

    return steps


def _auth_description(strategy: AuthStrategy) -> str:
    """Descripcion corta de la estrategia de auth para el plan."""
    mapping = {
        AuthStrategy.OAUTH2_RESOURCE_SERVER: "OAuth2 Resource Server (JWT)",
        AuthStrategy.API_GATEWAY_DELEGATED: "API Gateway delegated",
        AuthStrategy.MACHINE_TO_MACHINE: "Machine-to-machine",
        AuthStrategy.DEFERRED: "placeholder (deferred)",
    }
    return mapping[strategy]


def _file(path: str, description: str) -> dict:
    """Helper para crear entrada de archivo en el plan."""
    return {"path": path, "action": "create", "description": description}
