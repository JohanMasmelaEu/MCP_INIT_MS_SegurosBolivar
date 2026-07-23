"""Generador de proyectos Python 3.12 + FastAPI + uv.

Implementa la logica de renderizado y escritura de todos los archivos
del arquetipo Python/FastAPI basado en el blueprint TECH_STACK_BLUEPRINT_PYTHON.md.
"""

import json
import logging
from pathlib import Path

from src.generators.base import BaseGenerator
from src.models.project_config import DomainModule, ProjectConfig
from src.utils.file_writer import FileWriter
from src.utils.template_renderer import TemplateRenderer

logger = logging.getLogger("mcp_init_ms.generators.python_fastapi")

STACK_ID = "python-fastapi"


class PythonFastApiGenerator(BaseGenerator):
    """Genera proyectos Python 3.12 / FastAPI / SQLAlchemy async completos."""

    def __init__(self, config: ProjectConfig, project_root: Path) -> None:
        """Inicializa el generador Python/FastAPI.

        Args:
            config: Configuracion completa del proyecto.
            project_root: Directorio raiz donde se genera el proyecto.
        """
        super().__init__(config, project_root)
        self.renderer = TemplateRenderer(STACK_ID)
        self.ctx = self._build_context()

    def generate(self) -> list[Path]:
        """Genera el proyecto completo Python/FastAPI.

        Returns:
            Lista de archivos creados.
        """
        logger.info("Generando proyecto Python/FastAPI '%s' en %s", self.config.project_name, self.project_root)

        self._generate_pyproject()
        self._generate_git_files()
        self._generate_src_base()
        self._generate_config()
        self._generate_commons()
        self._generate_middleware()
        self._generate_errors()
        self._generate_utils()
        self._generate_tests_base()
        self._generate_infrastructure()
        self._generate_cicd()
        self._generate_documentation()
        self._generate_kiro_context()

        # Condicionales
        if self.config.use_pre_commit:
            self._generate_pre_commit()

        # Generar modulos de dominio
        for module in self.config.modules:
            self.generate_domain_module(module)

        # Persistir project-config.json
        self._persist_project_config()

        logger.info("Proyecto Python/FastAPI generado: %d archivos", len(self.writer.created_files))
        return self.writer.get_created_files()

    def generate_domain_module(self, module: DomainModule) -> list[Path]:
        """Genera un modulo de dominio CRUD completo para Python/FastAPI.

        Args:
            module: Configuracion del modulo a generar.

        Returns:
            Lista de archivos creados para este modulo.
        """
        initial_count = len(self.writer.created_files)
        mod = module.module_name
        module_ctx = {**self.ctx, "module": module, "m": module}

        # Package init
        self._render_write(
            "domain-module/__init__.py.j2",
            f"src/{mod}/__init__.py",
            module_ctx,
        )

        # Router
        self._render_write(
            "domain-module/router.py.j2",
            f"src/{mod}/router.py",
            module_ctx,
        )

        # Service
        self._render_write(
            "domain-module/service.py.j2",
            f"src/{mod}/service.py",
            module_ctx,
        )

        # Repository
        self._render_write(
            "domain-module/repository.py.j2",
            f"src/{mod}/repository.py",
            module_ctx,
        )

        # Models (SQLAlchemy)
        self._render_write(
            "domain-module/models.py.j2",
            f"src/{mod}/models.py",
            module_ctx,
        )

        # Schemas package
        self._render_write(
            "domain-module/schemas/__init__.py.j2",
            f"src/{mod}/schemas/__init__.py",
            module_ctx,
        )
        self._render_write(
            "domain-module/schemas/crear.py.j2",
            f"src/{mod}/schemas/crear.py",
            module_ctx,
        )
        self._render_write(
            "domain-module/schemas/actualizar.py.j2",
            f"src/{mod}/schemas/actualizar.py",
            module_ctx,
        )
        self._render_write(
            "domain-module/schemas/filtros.py.j2",
            f"src/{mod}/schemas/filtros.py",
            module_ctx,
        )
        self._render_write(
            "domain-module/schemas/response.py.j2",
            f"src/{mod}/schemas/response.py",
            module_ctx,
        )

        # Tests
        self._render_write(
            "domain-module/tests/__init__.py.j2",
            f"src/{mod}/tests/__init__.py",
            module_ctx,
        )
        self._render_write(
            "domain-module/tests/test_service.py.j2",
            f"src/{mod}/tests/test_service.py",
            module_ctx,
        )
        self._render_write(
            "domain-module/tests/test_router.py.j2",
            f"src/{mod}/tests/test_router.py",
            module_ctx,
        )

        return self.writer.created_files[initial_count:]

    def regenerate_infrastructure(self) -> list[Path]:
        """Regenera archivos de infraestructura (docker-compose, env, seed).

        Returns:
            Lista de archivos regenerados.
        """
        self.writer = FileWriter(self.project_root)
        self.ctx = self._build_context()
        self._generate_infrastructure()
        return self.writer.get_created_files()

    def _build_context(self) -> dict:
        """Construye el contexto base para todos los templates.

        Returns:
            Diccionario con todas las variables disponibles en templates Jinja2.
        """
        return {
            "config": self.config,
            "c": self.config,
            "stack": STACK_ID,
            "project_name": self.config.project_name,
            "context_path": self.config.context_path,
            "context_path_clean": self.config.context_path_clean,
            "api_description": self.config.api_description,
            "api_version": self.config.api_version,
            # Database
            "db": self.config.database,
            # Auth
            "auth_strategy": self.config.auth_strategy.value,
            # Integrations
            "integrations": self.config.integrations,
            # Observability
            "observability": self.config.observability,
            "dd_service": self.config.dd_service,
            # Modules
            "modules": self.config.modules,
            # Ports
            "app_port": self.config.app_port,
            "localstack_port": self.config.localstack_port,
            "redis_port": self.config.redis_port,
            # LocalStack
            "localstack_services": self.config.localstack_services,
            # Security
            "cors_allow_credentials": self.config.cors_allow_credentials,
            "extra_public_paths": self.config.extra_public_paths,
            # Metadata
            "cache": self.config.cache,
            "i18n": self.config.i18n,
            "artifactory_url": self.config.artifactory_url,
            # Python specific
            "mypy_strict": self.config.mypy_strict,
            "use_pre_commit": self.config.use_pre_commit,
            # SSM
            "ssm_app_prefix": self.config.ssm_app_prefix,
            # OpenAPI
            "openapi_path": self.config.openapi_path,
        }

    def _render_write(self, template_path: str, output_path: str, context: dict | None = None) -> None:
        """Renderiza un template y escribe el resultado.

        Args:
            template_path: Ruta del template Jinja2 relativa a templates/python-fastapi/.
            output_path: Ruta de salida relativa al proyecto.
            context: Contexto adicional (default: self.ctx).
        """
        ctx = context or self.ctx
        content = self.renderer.render(template_path, ctx)
        self.writer.write(output_path, content)

    def _generate_pyproject(self) -> None:
        """Genera pyproject.toml con dependencias condicionales y config de tools."""
        self._render_write("pyproject.toml.j2", "pyproject.toml")

    def _generate_git_files(self) -> None:
        """Genera .gitignore."""
        self._render_write("git/gitignore.j2", ".gitignore")

    def _generate_src_base(self) -> None:
        """Genera src/__init__.py y src/main.py (app factory)."""
        self._render_write("src/__init__.py.j2", "src/__init__.py")
        self._render_write("src/main.py.j2", "src/main.py")

    def _generate_config(self) -> None:
        """Genera src/config/ (settings, database, logging, security)."""
        self._render_write("src/config/__init__.py.j2", "src/config/__init__.py")
        self._render_write("src/config/settings.py.j2", "src/config/settings.py")
        self._render_write("src/config/database.py.j2", "src/config/database.py")
        self._render_write("src/config/logging.py.j2", "src/config/logging.py")
        self._render_write("src/config/security.py.j2", "src/config/security.py")

    def _generate_commons(self) -> None:
        """Genera src/commons/ (api_response, pagination, audit_mixin)."""
        self._render_write("src/commons/__init__.py.j2", "src/commons/__init__.py")
        self._render_write("src/commons/api_response.py.j2", "src/commons/api_response.py")
        self._render_write("src/commons/pagination.py.j2", "src/commons/pagination.py")
        self._render_write("src/commons/audit_mixin.py.j2", "src/commons/audit_mixin.py")

    def _generate_middleware(self) -> None:
        """Genera src/middleware/ (correlation_id, error_handler, request_logger, security_headers)."""
        self._render_write("src/middleware/__init__.py.j2", "src/middleware/__init__.py")
        self._render_write("src/middleware/correlation_id.py.j2", "src/middleware/correlation_id.py")
        self._render_write("src/middleware/error_handler.py.j2", "src/middleware/error_handler.py")
        self._render_write("src/middleware/request_logger.py.j2", "src/middleware/request_logger.py")
        self._render_write("src/middleware/security_headers.py.j2", "src/middleware/security_headers.py")

    def _generate_errors(self) -> None:
        """Genera src/errors/ (bolivar_business_error, error_types)."""
        self._render_write("src/errors/__init__.py.j2", "src/errors/__init__.py")
        self._render_write("src/errors/bolivar_business_error.py.j2", "src/errors/bolivar_business_error.py")
        self._render_write("src/errors/error_types.py.j2", "src/errors/error_types.py")

    def _generate_utils(self) -> None:
        """Genera src/utils/ (data_sanitizer, date_utils)."""
        self._render_write("src/utils/__init__.py.j2", "src/utils/__init__.py")
        self._render_write("src/utils/data_sanitizer.py.j2", "src/utils/data_sanitizer.py")
        self._render_write("src/utils/date_utils.py.j2", "src/utils/date_utils.py")

    def _generate_tests_base(self) -> None:
        """Genera tests/ base (conftest, factories)."""
        self._render_write("tests/__init__.py.j2", "tests/__init__.py")
        self._render_write("tests/conftest.py.j2", "tests/conftest.py")
        self._render_write("tests/factories/__init__.py.j2", "tests/factories/__init__.py")

    def _generate_infrastructure(self) -> None:
        """Genera Dockerfile, docker-compose, seed-ssm, .env.sample, .env."""
        self._render_write("infra/Dockerfile.j2", "Dockerfile")
        self._render_write("infra/docker-compose.yml.j2", "docker-compose.yml")
        self._render_write("infra/seed-localstack-ssm.sh.j2", "scripts/seed-localstack-ssm.sh")
        self._render_write("infra/env.sample.j2", ".env.sample")
        self._render_write("infra/env.j2", ".env")

        # Mock OAuth solo si la estrategia lo requiere
        if self.config.auth_strategy.value == "oauth2-resource-server":
            self._render_write("infra/mock-oauth-config.json.j2", "config/mock-oauth-config.json")

    def _generate_cicd(self) -> None:
        """Genera archivos CI/CD (GitHub Actions)."""
        self._render_write("cicd/pipeline.yaml.j2", ".github/workflows/pipeline.yaml")
        self._render_write("cicd/CODEOWNERS.j2", ".github/CODEOWNERS")
        self._render_write("cicd/pull_request_template.md.j2", ".github/pull_request_template.md")

    def _generate_documentation(self) -> None:
        """Genera README.md y api_spec.yaml."""
        self._render_write("docs/README.md.j2", "README.md")
        self._render_write("docs/api_spec.yaml.j2", "api_spec.yaml")

    def _generate_kiro_context(self) -> None:
        """Genera archivos .kiro/ completos: project.json, steering, hooks, changelogs."""
        from datetime import date

        ctx_with_date = {**self.ctx, "now_iso": date.today().isoformat()}

        # project.json
        self._render_write("kiro/project.json.j2", ".kiro/project.json", ctx_with_date)

        # Steering files (mismos 00-08 que Java + 10-stack-python)
        steering_files = [
            "00-org-conventions",
            "01-architecture",
            "02-security",
            "03-code-style",
            "04-testing-standards",
            "05-responsible-ai-use",
            "06-data-access",
            "07-error-handling",
            "08-observability",
            "10-stack-python",
        ]
        for name in steering_files:
            self._render_write(
                f"kiro/steering/{name}.md.j2",
                f".kiro/steering/{name}.md",
                ctx_with_date,
            )

        # Hooks (mismos 7, build-validate usa ruff check src/)
        hook_files = [
            "pre-write-gate",
            "responsible-use",
            "code-review-gate",
            "test-coverage-gate",
            "build-validate",
            "integrity-check",
            "summary-on-completion",
            "implementation-tracker",
        ]
        for name in hook_files:
            self._render_write(
                f"kiro/hooks/{name}.json.j2",
                f".kiro/hooks/{name}.json",
            )

        # Changelog
        self._render_write("kiro/changelog-develop.md.j2", ".kiro/changelogs/changelog-develop.md")

        # Implementation tracker
        self._render_write("kiro/implementation-log.json.j2", ".kiro/implementation-log.json", ctx_with_date)

        # MCP settings
        self._generate_kiro_mcp_settings()

    def _generate_kiro_mcp_settings(self) -> None:
        """Genera .kiro/settings/mcp.json con los MCPs seleccionados."""
        selected = self.config.selected_mcps

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

    def _generate_pre_commit(self) -> None:
        """Genera .pre-commit-config.yaml."""
        self._render_write("pre-commit/pre-commit-config.yaml.j2", ".pre-commit-config.yaml")

    def _persist_project_config(self) -> None:
        """Persiste la configuracion del proyecto en .kiro/project-config.json."""
        config_json = json.dumps(self.config.model_dump(mode="json"), ensure_ascii=False, indent=2)
        self.writer.write(".kiro/project-config.json", config_json)
