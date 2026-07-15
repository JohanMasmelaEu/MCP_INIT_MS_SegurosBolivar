"""Generador de proyectos Java 21 / Spring Boot 4.x / Gradle.

Implementa la logica de renderizado y escritura de todos los archivos
del arquetipo basado en el proyecto CUC como pivote.
"""

import json
import logging
from pathlib import Path

from src.generators.base import BaseGenerator
from src.models.project_config import DomainModule, ProjectConfig
from src.utils.file_writer import FileWriter
from src.utils.template_renderer import TemplateRenderer

logger = logging.getLogger("mcp_init_ms.generators.java_spring_boot")

STACK_ID = "java-spring-boot"
RULES_DIR = Path(__file__).resolve().parent.parent.parent / "rules"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


class JavaSpringBootGenerator(BaseGenerator):
    """Genera proyectos Java 21 / Spring Boot 4.x completos."""

    def __init__(self, config: ProjectConfig, project_root: Path) -> None:
        """Inicializa el generador Java/Spring Boot.

        Args:
            config: Configuracion completa del proyecto.
            project_root: Ruta donde se genera el proyecto.
        """
        super().__init__(config, project_root)
        self.renderer = TemplateRenderer(STACK_ID)
        self.ctx = self._build_context()

    def generate(self) -> list[Path]:
        """Genera el proyecto completo.

        Returns:
            Lista de archivos creados.
        """
        logger.info("Generando proyecto '%s' en %s", self.config.project_name, self.project_root)

        self._generate_gradle()
        self._generate_git_files()
        self._generate_java_base()
        self._generate_commons()
        self._generate_config()
        self._generate_security()
        self._generate_entities_base()
        self._generate_errorhandling()
        self._generate_utils()
        self._generate_resources()
        self._generate_test_base()
        self._generate_infrastructure()
        self._generate_cicd()
        self._generate_documentation()
        self._generate_kiro_context()

        # Generar modulos de dominio
        for module in self.config.modules:
            self.generate_domain_module(module)

        # Generar configs opcionales de integraciones
        self._generate_integrations()

        # Persistir project-config.json para tools posteriores
        self._persist_project_config()

        logger.info("Proyecto generado: %d archivos", len(self.writer.created_files))
        return self.writer.get_created_files()

    def generate_domain_module(self, module: DomainModule) -> list[Path]:
        """Genera un modulo de dominio completo.

        Args:
            module: Configuracion del modulo.

        Returns:
            Lista de archivos creados para este modulo.
        """
        initial_count = len(self.writer.created_files)
        module_ctx = {**self.ctx, "module": module, "m": module}

        pkg = self.config.base_package_path
        mod = module.module_name

        # Recolectar imports necesarios para los campos
        field_imports = set()
        for field in module.fields:
            imp = self.renderer.env.filters["java_type_import"](field.field_type.value)
            if imp:
                field_imports.add(imp)
        module_ctx["field_imports"] = sorted(field_imports)

        # Controller
        self._render_write(
            "domain-module/Controller.java.j2",
            f"src/main/java/{pkg}/{mod}/controller/{module.entity_name}Controller.java",
            module_ctx,
        )

        # DTOs
        for dto_template in ["CrearRequestDTO", "ActualizarRequestDTO", "FiltrosRequestDTO", "ResponseDTO"]:
            self._render_write(
                f"domain-module/dto/{dto_template}.java.j2",
                f"src/main/java/{pkg}/{mod}/dto/{module.entity_name}{dto_template}.java",
                module_ctx,
            )

        # Service interface + impl
        self._render_write(
            "domain-module/Service.java.j2",
            f"src/main/java/{pkg}/{mod}/services/{module.entity_name}Service.java",
            module_ctx,
        )
        self._render_write(
            "domain-module/ServiceImpl.java.j2",
            f"src/main/java/{pkg}/{mod}/services/{module.entity_name}ServiceImpl.java",
            module_ctx,
        )

        # Repository + Specification
        self._render_write(
            "domain-module/Repository.java.j2",
            f"src/main/java/{pkg}/{mod}/repository/{module.entity_name}Repository.java",
            module_ctx,
        )
        self._render_write(
            "domain-module/Specification.java.j2",
            f"src/main/java/{pkg}/{mod}/repository/{module.entity_name}Specification.java",
            module_ctx,
        )

        # Entity
        self._render_write(
            "domain-module/Entity.java.j2",
            f"src/main/java/{pkg}/entity/{module.entity_name}.java",
            module_ctx,
        )

        # Tests
        self._render_write(
            "domain-module/ControllerTest.java.j2",
            f"src/test/java/{pkg}/{mod}/controller/{module.entity_name}ControllerTest.java",
            module_ctx,
        )
        self._render_write(
            "domain-module/ServiceTest.java.j2",
            f"src/test/java/{pkg}/{mod}/services/{module.entity_name}ServiceTest.java",
            module_ctx,
        )

        return self.writer.created_files[initial_count:]

    def regenerate_infrastructure(self) -> list[Path]:
        """Regenera archivos de infraestructura local.

        Returns:
            Lista de archivos regenerados.
        """
        # Reset writer para rastrear solo lo nuevo
        self.writer = FileWriter(self.project_root)
        self.ctx = self._build_context()
        self._generate_infrastructure()
        return self.writer.get_created_files()

    def _build_context(self) -> dict:
        """Construye el contexto base para todos los templates.

        Returns:
            Diccionario con todas las variables disponibles en templates.
        """
        return {
            "config": self.config,
            "c": self.config,
            "project_name": self.config.project_name,
            "base_package": self.config.base_package,
            "base_package_path": self.config.base_package_path,
            "application_class": self.config.application_class_name,
            "configuration_class": self.config.configuration_class_name,
            "context_path": self.config.context_path,
            "context_path_clean": self.config.context_path_clean,
            "artifact_name": self.config.artifact_name,
            "group_id": self.config.group_id,
            "api_description": self.config.api_description,
            "api_version": self.config.api_version,
            "db": self.config.database,
            "auth_strategy": self.config.auth_strategy.value,
            "integrations": self.config.integrations,
            "observability": self.config.observability,
            "dd_service": self.config.dd_service,
            "openapi_path": self.config.openapi_path,
            "ssm_app_prefix": self.config.ssm_app_prefix,
            "artifactory_url": self.config.artifactory_url,
            "modules": self.config.modules,
        }

    def _render_write(self, template_path: str, output_path: str, context: dict | None = None) -> None:
        """Renderiza un template y escribe el resultado.

        Args:
            template_path: Ruta del template Jinja2.
            output_path: Ruta de salida relativa al proyecto.
            context: Contexto adicional (default: self.ctx).
        """
        ctx = context or self.ctx
        content = self.renderer.render(template_path, ctx)
        self.writer.write(output_path, content)

    def _generate_gradle(self) -> None:
        """Genera archivos Gradle."""
        self._render_write("gradle/build.gradle.j2", "build.gradle")
        self._render_write("gradle/settings.gradle.j2", "settings.gradle")
        self._render_write("gradle/gradlew.j2", "gradlew")
        self._render_write("gradle/gradlew.bat.j2", "gradlew.bat")
        self._render_write("gradle/gradle-wrapper.properties.j2", "gradle/wrapper/gradle-wrapper.properties")

    def _generate_git_files(self) -> None:
        """Genera archivos Git (.gitignore, .gitattributes)."""
        self._render_write("git/gitignore.j2", ".gitignore")
        self._render_write("git/gitattributes.j2", ".gitattributes")

    def _generate_java_base(self) -> None:
        """Genera clases Java base (Application, Configuration)."""
        pkg = self.config.base_package_path
        self._render_write("src/Application.java.j2", f"src/main/java/{pkg}/{self.config.application_class_name}.java")
        self._render_write("src/Configuration.java.j2", f"src/main/java/{pkg}/{self.config.configuration_class_name}.java")

    def _generate_commons(self) -> None:
        """Genera paquete commons/ (DTOs transversales)."""
        pkg = self.config.base_package_path
        for name in ["ApiResponseDTO", "ApiResponseData", "ApiResponseMensajes", "UsuarioAuditoriaProvider"]:
            self._render_write(f"src/commons/{name}.java.j2", f"src/main/java/{pkg}/commons/{name}.java")

    def _generate_config(self) -> None:
        """Genera paquete config/ (configuraciones transversales)."""
        pkg = self.config.base_package_path
        configs = [
            "DataBaseConfiguration",
            "ParameterStoreClient",
            "SsmParameterStoreConfiguration",
            "OpenApiConfiguration",
            "WebClientConfiguration",
            "HtmlEntitiesJacksonConfiguration",
            "JsonUtf8Configuration",
        ]
        for name in configs:
            self._render_write(f"src/config/{name}.java.j2", f"src/main/java/{pkg}/config/{name}.java")

    def _generate_security(self) -> None:
        """Genera paquete config/security/ (Spring Security)."""
        pkg = self.config.base_package_path
        security_classes = [
            "SecurityConfig",
            "SecurityHeadersFilter",
            "ApiErrorAccessDeniedHandler",
            "ApiErrorAuthenticationEntryPoint",
        ]
        for name in security_classes:
            self._render_write(f"src/config/security/{name}.java.j2", f"src/main/java/{pkg}/config/security/{name}.java")

    def _generate_entities_base(self) -> None:
        """Genera MappedSuperclasses de auditoria."""
        pkg = self.config.base_package_path
        for name in ["AuditoriaCompleta", "AuditoriaSoloCreacion"]:
            self._render_write(f"src/entity/{name}.java.j2", f"src/main/java/{pkg}/entity/{name}.java")

    def _generate_errorhandling(self) -> None:
        """Genera paquete errorhandling/."""
        pkg = self.config.base_package_path
        classes = [
            "BolivarBusinessException",
            "GlobalExceptionHandler",
            "TipoErrorEnum",
            "ValidationExceptionHandler",
        ]
        for name in classes:
            self._render_write(f"src/errorhandling/{name}.java.j2", f"src/main/java/{pkg}/errorhandling/{name}.java")

    def _generate_utils(self) -> None:
        """Genera paquete utils/."""
        pkg = self.config.base_package_path
        for name in ["DataSanitizer", "HtmlEntityEncoder"]:
            self._render_write(f"src/utils/{name}.java.j2", f"src/main/java/{pkg}/utils/{name}.java")

    def _generate_resources(self) -> None:
        """Genera archivos de configuracion Spring (resources/)."""
        self._render_write("resources/application.yaml.j2", "src/main/resources/application.yaml")
        self._render_write("resources/application-local.yaml.j2", "src/main/resources/application-local.yaml")
        self._render_write("resources/application-test.yaml.j2", "src/main/resources/application-test.yaml")

    def _generate_test_base(self) -> None:
        """Genera test base de carga de contexto."""
        pkg = self.config.base_package_path
        self._render_write(
            "test/ApplicationTest.java.j2",
            f"src/test/java/{pkg}/{self.config.application_class_name}Test.java",
        )

    def _generate_infrastructure(self) -> None:
        """Genera archivos de infraestructura local (Docker, LocalStack, etc.)."""
        self._render_write("infra/Dockerfile.j2", "development/docker-local-ms/Dockerfile")
        self._render_write("infra/docker-compose.yml.j2", "development/docker-local-ms/docker-compose.yml")
        self._render_write("infra/down.ps1.j2", "development/docker-local-ms/down.ps1")
        self._render_write("infra/down.sh.j2", "development/docker-local-ms/down.sh")
        self._render_write("infra/seed-localstack-ssm.sh.j2", "development/docker-local-ms/scripts/seed-localstack-ssm.sh")
        self._render_write("infra/mock-oauth-config.json.j2", "development/docker-local-ms/config/mock-oauth-config.json")
        self._render_write("infra/env.sample.j2", "development/.env.sample")
        self._render_write("infra/env.j2", ".env")

    def _generate_cicd(self) -> None:
        """Genera archivos CI/CD (GitHub Actions)."""
        self._render_write("cicd/pipeline.yaml.j2", ".github/workflows/pipeline.yaml")
        self._render_write("cicd/pull-request.yml.j2", ".github/workflows/pull-request.yml")
        self._render_write("cicd/CODEOWNERS.j2", ".github/CODEOWNERS")
        self._render_write("cicd/pull_request_template.md.j2", ".github/pull_request_template.md")

    def _generate_documentation(self) -> None:
        """Genera documentacion del proyecto."""
        self._render_write("docs/README.md.j2", "README.md")
        self._render_write("docs/api_spec.yaml.j2", "api_spec.yaml")

    def _generate_kiro_context(self) -> None:
        """Genera archivos de contexto .kiro/ (steering, changelogs, hooks, mcp, specs)."""
        self._render_write("kiro/api-context.md.j2", ".kiro/steering/api-context.md")
        self._render_write("kiro/changelog-develop.md.j2", ".kiro/changelogs/changelog-develop.md")

        # Copiar rules transversales
        if RULES_DIR.exists():
            for rule_file in RULES_DIR.glob("*.md"):
                content = rule_file.read_text(encoding="utf-8")
                self.writer.write(f".kiro/steering/{rule_file.name}", content)

        # Generar hooks por stack
        self._generate_kiro_hooks()

        # Generar .kiro/settings/mcp.json con MCPs seleccionados del marketplace
        self._generate_kiro_mcp_settings()

        # Generar spec inicial del proyecto
        self._generate_kiro_specs()

    def _generate_kiro_hooks(self) -> None:
        """Genera hooks de Kiro segun el stack (archivos .kiro/hooks/*.json)."""
        hooks_template_dir = TEMPLATES_DIR / "java-spring-boot" / "kiro" / "hooks"
        if not hooks_template_dir.exists():
            return

        for hook_template in hooks_template_dir.glob("*.json.j2"):
            hook_name = hook_template.stem  # ej: compile-on-save.json
            content = self.renderer.render(f"kiro/hooks/{hook_template.name}", self.ctx)
            self.writer.write(f".kiro/hooks/{hook_name}", content)

    def _generate_kiro_mcp_settings(self) -> None:
        """Genera .kiro/settings/mcp.json con los MCPs seleccionados del marketplace."""
        selected = self.config.selected_mcps

        # Si no se selecciono nada, incluir MCP_INIT por defecto
        if not selected:
            selected = [
                {
                    "id": "MCP_INIT_MS_SegurosBolivar",
                    "docker_args": [
                        "run", "-i", "--rm",
                        "-v", "C:/REPOS:/repos",
                        "-v", "mcp-init-settings:/settings",
                        "-p", "9752:9752",
                        "ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest",
                    ],
                }
            ]
        else:
            selected = [m.model_dump() for m in selected]

        ctx = {**self.ctx, "selected_mcps": selected}
        content = self.renderer.render("kiro/mcp-settings.json.j2", ctx)
        self.writer.write(".kiro/settings/mcp.json", content)

    def _generate_kiro_specs(self) -> None:
        """Genera spec inicial del proyecto basado en la configuracion."""
        ctx = {**self.ctx, "config": self.config}
        content = self.renderer.render("kiro/specs/project-initialization.md.j2", ctx)
        self.writer.write(".kiro/specs/project-initialization.md", content)

    def _generate_integrations(self) -> None:
        """Genera configuraciones de integraciones opcionales."""
        pkg = self.config.base_package_path

        if self.config.integrations.uses_s3:
            self._render_write("src/config/S3Configuration.java.j2", f"src/main/java/{pkg}/config/S3Configuration.java")
            self._render_write("src/config/S3Properties.java.j2", f"src/main/java/{pkg}/config/S3Properties.java")

        if self.config.integrations.uses_sqs:
            self._render_write("src/config/SqsConfiguration.java.j2", f"src/main/java/{pkg}/config/SqsConfiguration.java")

        if self.config.integrations.uses_soap:
            self._render_write("src/config/WsSecurityConfiguration.java.j2", f"src/main/java/{pkg}/config/WsSecurityConfiguration.java")

    def _persist_project_config(self) -> None:
        """Persiste la configuracion del proyecto en .kiro/project-config.json."""
        config_json = json.dumps(self.config.model_dump(mode="json"), ensure_ascii=False, indent=2)
        self.writer.write(".kiro/project-config.json", config_json)
