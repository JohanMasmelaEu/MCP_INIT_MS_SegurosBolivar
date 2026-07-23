"""Modelos Pydantic para la configuracion de proyectos generados por el MCP.

Estos modelos validan el input del usuario antes de pasar a la generacion.
Cada modelo representa una categoria de configuracion.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AuthStrategy(str, Enum):
    """Estrategias de autenticacion soportadas."""

    OAUTH2_RESOURCE_SERVER = "oauth2-resource-server"
    API_GATEWAY_DELEGATED = "api-gateway-delegated"
    MACHINE_TO_MACHINE = "machine-to-machine"
    DEFERRED = "deferred"


class FieldType(str, Enum):
    """Tipos de campo soportados para entidades JPA."""

    STRING = "String"
    LONG = "Long"
    INTEGER = "Integer"
    BOOLEAN = "Boolean"
    BIG_DECIMAL = "BigDecimal"
    LOCAL_DATE = "LocalDate"
    LOCAL_DATE_TIME = "LocalDateTime"
    UUID = "UUID"


class EntityField(BaseModel):
    """Define un campo de una entidad JPA."""

    name: str = Field(description="Nombre del campo en Java (camelCase)")
    field_type: FieldType = Field(description="Tipo Java del campo")
    column_name: str = Field(description="Nombre de la columna en BD (snake_case)")
    nullable: bool = Field(default=True, description="Si el campo acepta null")
    length: Optional[int] = Field(default=None, description="Longitud maxima (solo para String)")
    unique: bool = Field(default=False, description="Si el campo tiene restriccion unique")
    description: Optional[str] = Field(default=None, description="Descripcion del campo para OpenAPI")


class DomainModule(BaseModel):
    """Configuracion de un modulo de dominio (un recurso REST completo)."""

    module_name: str = Field(
        description="Nombre del modulo en lowercase (ej: polizas, siniestros)",
        pattern=r"^[a-z][a-z0-9]*$",
    )
    entity_name: str = Field(
        description="Nombre de la entidad JPA en PascalCase (ej: Poliza, Siniestro)",
        pattern=r"^[A-Z][a-zA-Z0-9]*$",
    )
    table_name: str = Field(
        description="Nombre de la tabla en BD UPPER_CASE (ej: POLIZA, SINIESTRO)",
        pattern=r"^[A-Z][A-Z0-9_]*$",
    )
    resource_path: Optional[str] = Field(
        default=None,
        description="Path REST del recurso (ej: polizas). Si no se indica, se usa module_name",
    )
    fields: list[EntityField] = Field(
        default_factory=list,
        description="Campos de la entidad (sin id, cod, ni auditoria; esos se generan automaticamente)",
    )
    has_cod_field: bool = Field(
        default=True,
        description="Si la entidad tiene un campo cod_<entidad> autogenerado (patron CUC)",
    )

    @property
    def resource_path_resolved(self) -> str:
        """Path REST del recurso, derivado del module_name si no se especifica."""
        return self.resource_path or self.module_name


class DatabaseConfig(BaseModel):
    """Configuracion de la base de datos PostgreSQL."""

    db_name: str = Field(description="Nombre de la base de datos PostgreSQL")
    db_schema: str = Field(default="public", description="Schema de la BD")
    db_user: str = Field(description="Usuario de la BD (local)")
    db_password: str = Field(description="Contrasena de la BD (local)")
    db_port: int = Field(default=5433, description="Puerto PostgreSQL local")
    ssm_prefix: Optional[str] = Field(
        default=None,
        description="Prefijo SSM para los parametros de BD (ej: /miservicio/dev). Si no se indica, se genera.",
    )
    ssm_endpoint_path: Optional[str] = Field(default=None, description="Ruta SSM del endpoint BD")
    ssm_dbname_path: Optional[str] = Field(default=None, description="Ruta SSM del nombre de BD")
    ssm_username_path: Optional[str] = Field(default=None, description="Ruta SSM del usuario")
    ssm_password_path: Optional[str] = Field(default=None, description="Ruta SSM de la contrasena")

    @property
    def ssm_endpoint_resolved(self) -> str:
        """Ruta SSM del endpoint BD, derivada del prefix si no se especifica."""
        return self.ssm_endpoint_path or f"{self.ssm_prefix or '/app/dev'}/database/endpoint"

    @property
    def ssm_dbname_resolved(self) -> str:
        """Ruta SSM del nombre BD, derivada del prefix si no se especifica."""
        return self.ssm_dbname_path or f"{self.ssm_prefix or '/app/dev'}/database/dbname"

    @property
    def ssm_username_resolved(self) -> str:
        """Ruta SSM del usuario BD, derivada del prefix si no se especifica."""
        return self.ssm_username_path or f"{self.ssm_prefix or '/app/dev'}/database/username"

    @property
    def ssm_password_resolved(self) -> str:
        """Ruta SSM de la password BD, derivada del prefix si no se especifica."""
        return self.ssm_password_path or f"{self.ssm_prefix or '/app/dev'}/database/password"


class ExternalHttpService(BaseModel):
    """Configuracion de un servicio HTTP externo a consumir."""

    name: str = Field(description="Nombre identificador del servicio (camelCase)")
    base_url_env_var: str = Field(description="Variable de entorno para la URL base")
    description: str = Field(description="Descripcion del servicio")
    requires_oauth: bool = Field(default=False, description="Si requiere token OAuth para consumir")


class IntegrationsConfig(BaseModel):
    """Configuracion de integraciones con servicios AWS y externos."""

    uses_s3: bool = Field(default=False, description="Requiere AWS S3 (archivos, presigned URLs)")
    uses_sqs: bool = Field(default=False, description="Requiere AWS SQS (colas de mensajes)")
    uses_soap: bool = Field(default=False, description="Requiere integraciones SOAP/WS legacy")
    external_http_services: list[ExternalHttpService] = Field(
        default_factory=list,
        description="Servicios HTTP externos a consumir via WebClient",
    )


class ObservabilityConfig(BaseModel):
    """Configuracion de observabilidad local (Datadog Agent no-forward)."""

    datadog_enabled: bool = Field(
        default=True,
        description="Incluir Datadog Agent local sin forward a cloud",
    )
    dd_service_name: Optional[str] = Field(
        default=None,
        description="Nombre del servicio en Datadog. Si no se indica, se usa el nombre del MS.",
    )


class McpServerSelection(BaseModel):
    """Seleccion de un MCP Server del marketplace para incluir en el proyecto."""

    id: str = Field(description="Identificador unico del MCP Server (ej: MCP_INIT_MS_SegurosBolivar)")
    docker_args: list[str] = Field(
        default_factory=list,
        description="Args de Docker para el MCP Server (se usan en .kiro/settings/mcp.json)",
    )


class ProjectConfig(BaseModel):
    """Configuracion completa del proyecto a generar.

    Este es el modelo raiz que agrupa todas las categorias de configuracion.
    """

    # --- Stack tecnologico ---
    stack: str = Field(
        default="java-spring-boot",
        description="Stack tecnologico del proyecto (java-spring-boot, node-express, python-fastapi).",
    )

    # --- Identidad del proyecto ---
    project_name: str = Field(
        description="Nombre del microservicio (ej: gestion-polizas-ms)",
        pattern=r"^[a-z][a-z0-9-]+-ms$",
    )
    group_id: str = Field(
        default="com.bolivar.comunes",
        description="Grupo Gradle/Maven (ej: com.bolivar.comunes). Solo aplica para Java.",
    )
    context_path: str = Field(
        description="Context-path del servlet / base path del API (ej: /gestion_polizas)",
        pattern=r"^/[a-z_][a-z0-9_]*$",
    )
    api_description: str = Field(
        description="Descripcion del API para OpenAPI/Swagger",
    )
    api_version: str = Field(default="1.0.0", description="Version del API")

    # --- Modulos de dominio ---
    modules: list[DomainModule] = Field(
        default_factory=list,
        description="Modulos de dominio a generar (cada uno es un CRUD completo)",
    )

    # --- Base de datos ---
    database: DatabaseConfig = Field(description="Configuracion de PostgreSQL")

    # --- Autenticacion ---
    auth_strategy: AuthStrategy = Field(
        default=AuthStrategy.DEFERRED,
        description="Estrategia de autenticacion del MS",
    )

    # --- Integraciones ---
    integrations: IntegrationsConfig = Field(
        default_factory=IntegrationsConfig,
        description="Integraciones con servicios AWS y HTTP externos",
    )

    # --- Observabilidad ---
    observability: ObservabilityConfig = Field(
        default_factory=ObservabilityConfig,
        description="Configuracion de observabilidad local",
    )

    # --- Artifactory ---
    artifactory_url: str = Field(
        default="https://segurosbolivar.jfrog.io/artifactory",
        description="URL base de JFrog Artifactory",
    )

    # --- MCP Servers (Marketplace) ---
    selected_mcps: list[McpServerSelection] = Field(
        default_factory=list,
        description="MCP Servers seleccionados del marketplace para incluir en .kiro/settings/mcp.json",
    )

    # --- Metadatos adicionales del proyecto ---
    i18n: list[str] = Field(
        default_factory=lambda: ["es"],
        description="Idiomas activos para mensajes (es, en). Default solo español.",
    )
    cache: Optional[str] = Field(
        default=None,
        description="Tecnología de cache si aplica (ej: 'redis'). None = sin cache.",
    )
    docker_profile: Optional[str] = Field(
        default=None,
        description="Perfil de imagen Docker (ej: 'java-redis'). Define qué incluye la imagen.",
    )

    # --- Puertos locales (evitar colisiones entre MS del mismo ecosistema) ---
    app_port: int = Field(
        default=8080,
        description="Puerto HTTP de la app en local. Cambiar si otro MS ya usa 8080.",
    )
    localstack_port: int = Field(
        default=4566,
        description="Puerto de LocalStack. Cambiar si otro MS ya usa 4566.",
    )
    redis_port: int = Field(
        default=6379,
        description="Puerto Redis local. Solo aplica si cache='redis'.",
    )

    # --- LocalStack services ---
    localstack_services: list[str] = Field(
        default_factory=lambda: ["ssm"],
        description="Servicios AWS a simular en LocalStack (ssm, secretsmanager, s3, sqs, events).",
    )

    # --- OpenAPI path custom ---
    openapi_base_path: Optional[str] = Field(
        default=None,
        description="Path custom para documentacion OpenAPI. Si no se indica, se genera automaticamente.",
    )

    # --- CORS ---
    cors_allow_credentials: bool = Field(
        default=True,
        description="allowCredentials en CORS. False para APIs M2M sin cookies.",
    )

    # --- Endpoints publicos adicionales (sin auth) ---
    extra_public_paths: list[str] = Field(
        default_factory=list,
        description="Paths adicionales que no requieren autenticacion (ej: /api/v1/auth/token).",
    )

    # --- Node specific ---
    typescript_strict: bool = Field(
        default=True,
        description="TypeScript strict mode en tsconfig. Solo aplica para node-express.",
    )
    use_husky: bool = Field(
        default=True,
        description="Incluir Husky + lint-staged para pre-commit. Solo aplica para node-express.",
    )
    npm_scope: Optional[str] = Field(
        default=None,
        description="Scope npm (ej: @bolivar). None = sin scope. Solo aplica para node-express.",
    )
    use_npmrc: bool = Field(
        default=False,
        description="Generar .npmrc con registry Artifactory. Solo aplica para node-express.",
    )

    # --- Python specific ---
    mypy_strict: bool = Field(
        default=True,
        description="mypy --strict en config. Solo aplica para python-fastapi.",
    )
    use_pre_commit: bool = Field(
        default=True,
        description="Incluir pre-commit hooks (ruff + mypy). Solo aplica para python-fastapi.",
    )

    @field_validator("project_name")
    @classmethod
    def validate_project_name_ends_with_ms(cls, v: str) -> str:
        """Valida que el nombre del proyecto termine en -ms."""
        if not v.endswith("-ms"):
            raise ValueError("El nombre del proyecto debe terminar en '-ms'")
        return v

    @property
    def base_package(self) -> str:
        """Paquete base Java derivado del group_id y nombre del proyecto.

        Ej: com.bolivar.gestion_polizas_ms
        """
        artifact = self.project_name.replace("-", "_")
        return f"com.bolivar.{artifact}"

    @property
    def base_package_path(self) -> str:
        """Ruta de directorios del paquete base.

        Ej: com/bolivar/gestion_polizas_ms
        """
        return self.base_package.replace(".", "/")

    @property
    def application_class_name(self) -> str:
        """Nombre de la clase Application en PascalCase.

        Ej: GestionPolizasMsApplication
        """
        parts = self.project_name.split("-")
        return "".join(p.capitalize() for p in parts) + "Application"

    @property
    def configuration_class_name(self) -> str:
        """Nombre de la clase Configuration en PascalCase.

        Ej: GestionPolizasMsConfiguration
        """
        parts = self.project_name.split("-")
        return "".join(p.capitalize() for p in parts) + "Configuration"

    @property
    def context_path_clean(self) -> str:
        """Context-path sin la barra inicial (para nombres internos).

        Ej: gestion_polizas
        """
        return self.context_path.lstrip("/")

    @property
    def artifact_name(self) -> str:
        """Nombre del artefacto (settings.gradle rootProject.name).

        Ej: gestion-polizas-ms
        """
        return self.project_name

    @property
    def ssm_app_prefix(self) -> str:
        """Prefijo SSM para la aplicacion.

        Ej: /gestionpolizas
        """
        clean = self.project_name.replace("-ms", "").replace("-", "")
        return f"/{clean}"

    @property
    def dd_service(self) -> str:
        """Nombre del servicio para Datadog.

        Ej: gestion-polizas-ms
        """
        return self.observability.dd_service_name or self.project_name

    @property
    def openapi_path(self) -> str:
        """Path del endpoint OpenAPI JSON.

        Si openapi_base_path esta definido, lo usa directamente.
        Si no, genera uno automatico: /srv-{nombre_limpio}-openapi.
        """
        if self.openapi_base_path:
            return self.openapi_base_path
        clean = self.project_name.replace("-ms", "").replace("-", "")
        return f"/srv-{clean}-openapi"
