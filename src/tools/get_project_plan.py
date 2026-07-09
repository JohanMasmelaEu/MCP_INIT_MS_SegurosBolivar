"""Tool: get_project_plan — genera el plan detallado de archivos sin ejecutar."""

from src.models.project_config import AuthStrategy, ProjectConfig


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
        "target_directory": config.project_name,
        "total_files": len(files),
        "total_directories": len(set(f["path"].rsplit("/", 1)[0] for f in files if "/" in f["path"])),
        "tree": files,
        "decisions_made": decisions,
        "next_steps_after_generation": next_steps,
    }


def _build_file_tree(config: ProjectConfig) -> list[dict]:
    """Construye la lista de archivos que se generarian."""
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
        _file(f"{p}/development/docker-local-ms/config/mock-oauth-config.json", "Config Mock OAuth Server"),
        _file(f"{p}/development/.env.sample", "Template de variables de entorno"),
    ])

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
        _file(f"{p}/.kiro/steering/api-context.md", "Steering: contexto del API para Kiro"),
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


def _build_decisions(config: ProjectConfig) -> list[str]:
    """Lista de decisiones arquitectonicas tomadas."""
    decisions = []

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

    return decisions


def _build_next_steps(config: ProjectConfig) -> list[str]:
    """Pasos siguientes despues de la generacion."""
    steps = [
        f"1. Copiar development/.env.sample a .env y configurar ARTIFACTORY_USER / ARTIFACTORY_PASSWORD",
        f"2. Levantar infraestructura: cd {config.project_name}/development/docker-local-ms && docker compose --env-file ../../.env up -d",
        f"3. Verificar Swagger UI: http://localhost:8080{config.context_path}/swagger-ui.html",
        f"4. Verificar health: http://localhost:8080{config.context_path}/actuator/health",
    ]

    if config.observability.datadog_enabled:
        steps.append("5. Verificar Datadog Agent: docker logs <ms>-dd-agent | grep 'Trace received'")

    steps.append(f"{'6' if config.observability.datadog_enabled else '5'}. Implementar logica de negocio en los ServiceImpl")

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
