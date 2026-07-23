"""Generador de proyectos Node.js 22 + Express 4.x + TypeScript 5.x.

Implementa la logica de renderizado y escritura de todos los archivos
del arquetipo Node/Express basado en el blueprint TECH_STACK_BLUEPRINT_NODE.md.
"""

import json
import logging
from pathlib import Path

from src.generators.base import BaseGenerator
from src.models.project_config import DomainModule, ProjectConfig
from src.utils.file_writer import FileWriter
from src.utils.template_renderer import TemplateRenderer

logger = logging.getLogger("mcp_init_ms.generators.node_express")

STACK_ID = "node-express"


class NodeExpressGenerator(BaseGenerator):
    """Genera proyectos Node.js 22 / Express 4.x / TypeScript completos."""

    def __init__(self, config: ProjectConfig, project_root: Path) -> None:
        """Inicializa el generador Node/Express.

        Args:
            config: Configuracion completa del proyecto.
            project_root: Directorio raiz donde se genera el proyecto.
        """
        super().__init__(config, project_root)
        self.renderer = TemplateRenderer(STACK_ID)
        self.ctx = self._build_context()

    def generate(self) -> list[Path]:
        """Genera el proyecto completo Node/Express.

        Returns:
            Lista de archivos creados.
        """
        logger.info("Generando proyecto Node/Express '%s' en %s", self.config.project_name, self.project_root)

        self._generate_package_json()
        self._generate_tsconfig()
        self._generate_vitest_config()
        self._generate_eslint_prettier()
        self._generate_git_files()
        self._generate_src_base()
        self._generate_config()
        self._generate_commons()
        self._generate_middleware()
        self._generate_errors()
        self._generate_utils()
        self._generate_test_helpers()
        self._generate_infrastructure()
        self._generate_cicd()
        self._generate_documentation()
        self._generate_kiro_context()

        # Condicionales
        if self.config.use_husky:
            self._generate_husky()
        if self.config.use_npmrc:
            self._generate_npmrc()

        # Generar modulos de dominio
        for module in self.config.modules:
            self.generate_domain_module(module)

        # Persistir project-config.json
        self._persist_project_config()

        logger.info("Proyecto Node/Express generado: %d archivos", len(self.writer.created_files))
        return self.writer.get_created_files()

    def generate_domain_module(self, module: DomainModule) -> list[Path]:
        """Genera un modulo de dominio CRUD completo para Node/Express.

        Args:
            module: Configuracion del modulo a generar.

        Returns:
            Lista de archivos creados para este modulo.
        """
        initial_count = len(self.writer.created_files)
        mod = module.module_name
        module_ctx = {**self.ctx, "module": module, "m": module}

        # Controller (router)
        self._render_write(
            "domain-module/controller.ts.j2",
            f"src/{mod}/{mod}.controller.ts",
            module_ctx,
        )

        # Service
        self._render_write(
            "domain-module/service.ts.j2",
            f"src/{mod}/{mod}.service.ts",
            module_ctx,
        )

        # Repository
        self._render_write(
            "domain-module/repository.ts.j2",
            f"src/{mod}/{mod}.repository.ts",
            module_ctx,
        )

        # Schema (Drizzle table definition)
        self._render_write(
            "domain-module/schema.ts.j2",
            f"src/{mod}/{mod}.schema.ts",
            module_ctx,
        )

        # DTOs
        dto_templates = ["crear.dto.ts", "actualizar.dto.ts", "filtros.dto.ts", "response.dto.ts"]
        for dto in dto_templates:
            self._render_write(
                f"domain-module/dto/{dto}.j2",
                f"src/{mod}/dto/{dto}",
                module_ctx,
            )

        # Tests
        self._render_write(
            "domain-module/tests/service.test.ts.j2",
            f"src/{mod}/tests/{mod}.service.test.ts",
            module_ctx,
        )
        self._render_write(
            "domain-module/tests/controller.test.ts.j2",
            f"src/{mod}/tests/{mod}.controller.test.ts",
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
            # Node specific
            "typescript_strict": self.config.typescript_strict,
            "use_husky": self.config.use_husky,
            "npm_scope": self.config.npm_scope,
            "use_npmrc": self.config.use_npmrc,
            # SSM
            "ssm_app_prefix": self.config.ssm_app_prefix,
            # OpenAPI
            "openapi_path": self.config.openapi_path,
        }

    def _render_write(self, template_path: str, output_path: str, context: dict | None = None) -> None:
        """Renderiza un template y escribe el resultado.

        Args:
            template_path: Ruta del template Jinja2 relativa a templates/node-express/.
            output_path: Ruta de salida relativa al proyecto.
            context: Contexto adicional (default: self.ctx).
        """
        ctx = context or self.ctx
        content = self.renderer.render(template_path, ctx)
        self.writer.write(output_path, content)

    def _generate_package_json(self) -> None:
        """Genera package.json con dependencias condicionales."""
        self._render_write("package.json.j2", "package.json")

    def _generate_tsconfig(self) -> None:
        """Genera tsconfig.json con strict mode configurable."""
        self._render_write("tsconfig.json.j2", "tsconfig.json")

    def _generate_vitest_config(self) -> None:
        """Genera vitest.config.ts con coverage v8."""
        self._render_write("vitest.config.ts.j2", "vitest.config.ts")

    def _generate_eslint_prettier(self) -> None:
        """Genera configuracion de ESLint v9 flat + Prettier."""
        self._render_write("eslint.config.mjs.j2", "eslint.config.mjs")
        self._render_write("prettierrc.j2", ".prettierrc")

    def _generate_git_files(self) -> None:
        """Genera .gitignore y .gitattributes."""
        self._render_write("git/gitignore.j2", ".gitignore")
        self._render_write("git/gitattributes.j2", ".gitattributes")

    def _generate_src_base(self) -> None:
        """Genera app.ts y server.ts."""
        self._render_write("src/app.ts.j2", "src/app.ts")
        self._render_write("src/server.ts.j2", "src/server.ts")

    def _generate_config(self) -> None:
        """Genera src/config/ (index, database, logger, security)."""
        self._render_write("src/config/index.ts.j2", "src/config/index.ts")
        self._render_write("src/config/database.ts.j2", "src/config/database.ts")
        self._render_write("src/config/logger.ts.j2", "src/config/logger.ts")
        self._render_write("src/config/security.ts.j2", "src/config/security.ts")

    def _generate_commons(self) -> None:
        """Genera src/commons/ (api-response, pagination, audit mixin)."""
        self._render_write("src/commons/api-response.dto.ts.j2", "src/commons/api-response.dto.ts")
        self._render_write("src/commons/pagination.dto.ts.j2", "src/commons/pagination.dto.ts")
        self._render_write("src/commons/audit.mixin.ts.j2", "src/commons/audit.mixin.ts")

    def _generate_middleware(self) -> None:
        """Genera src/middleware/ (error-handler, correlation-id, request-logger, validate, auth)."""
        self._render_write("src/middleware/error-handler.ts.j2", "src/middleware/error-handler.ts")
        self._render_write("src/middleware/correlation-id.ts.j2", "src/middleware/correlation-id.ts")
        self._render_write("src/middleware/request-logger.ts.j2", "src/middleware/request-logger.ts")
        self._render_write("src/middleware/validate.ts.j2", "src/middleware/validate.ts")
        self._render_write("src/middleware/auth.ts.j2", "src/middleware/auth.ts")

    def _generate_errors(self) -> None:
        """Genera src/errors/ (bolivar-business.error, error-types.enum)."""
        self._render_write("src/errors/bolivar-business.error.ts.j2", "src/errors/bolivar-business.error.ts")
        self._render_write("src/errors/error-types.enum.ts.j2", "src/errors/error-types.enum.ts")

    def _generate_utils(self) -> None:
        """Genera src/utils/ (data-sanitizer, date.utils)."""
        self._render_write("src/utils/data-sanitizer.ts.j2", "src/utils/data-sanitizer.ts")
        self._render_write("src/utils/date.utils.ts.j2", "src/utils/date.utils.ts")

    def _generate_test_helpers(self) -> None:
        """Genera tests/helpers/test-app.ts."""
        self._render_write("tests/helpers/test-app.ts.j2", "tests/helpers/test-app.ts")

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

        # Steering files (mismos 00-08 que Java + 10-stack-node)
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
            "10-stack-node",
        ]
        for name in steering_files:
            self._render_write(
                f"kiro/steering/{name}.md.j2",
                f".kiro/steering/{name}.md",
                ctx_with_date,
            )

        # Hooks (mismos 7, build-validate usa npm run lint)
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

    def _generate_husky(self) -> None:
        """Genera .husky/pre-commit y lint-staged config."""
        self._render_write("husky/pre-commit.j2", ".husky/pre-commit")

    def _generate_npmrc(self) -> None:
        """Genera .npmrc con registry Artifactory."""
        self._render_write("npmrc.j2", ".npmrc")

    def _persist_project_config(self) -> None:
        """Persiste la configuracion del proyecto en .kiro/project-config.json."""
        config_json = json.dumps(self.config.model_dump(mode="json"), ensure_ascii=False, indent=2)
        self.writer.write(".kiro/project-config.json", config_json)
