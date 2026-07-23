"""Tool: list_available_stacks — lista los stacks tecnologicos disponibles."""


def handle_list_available_stacks() -> dict:
    """Retorna los stacks soportados por el MCP.

    Returns:
        Diccionario con la lista de stacks, su estado y descripcion.
    """
    return {
        "stacks": [
            {
                "id": "java-spring-boot",
                "name": "Java 21 + Spring Boot 4.x + Gradle 9.x",
                "status": "available",
                "capabilities": ["generate", "blueprint", "add_module", "configure_infrastructure"],
                "description": (
                    "Microservicio Java con Spring Boot 4, Gradle, Spring Data JPA (PostgreSQL), "
                    "Spring Security (pluggable), SpringDoc OpenAPI, Docker Compose local "
                    "(LocalStack SSM/S3/SQS + Mock OAuth + Datadog Agent no-forward), "
                    "CI/CD GitHub Actions con templates institucionales Seguros Bolivar."
                ),
                "version": "1.0.0",
            },
            {
                "id": "node-express",
                "name": "Node.js 22 + Express 4.x + TypeScript 5.x",
                "status": "available",
                "capabilities": ["generate", "blueprint", "add_module", "configure_infrastructure"],
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
                "capabilities": ["generate", "blueprint", "add_module", "configure_infrastructure"],
                "description": (
                    "Microservicio Python con FastAPI, SQLAlchemy 2.x async (PostgreSQL), "
                    "Pydantic v2, structlog, uv package manager, Docker Compose local "
                    "(LocalStack + Redis + Datadog Agent no-forward), pytest + httpx, "
                    "Ruff + mypy, CI/CD GitHub Actions."
                ),
                "version": "1.0.0",
            },
        ],
        "note": (
            "Todos los stacks soportan generacion completa de proyecto, blueprints tecnicos, "
            "adicion de modulos de dominio y configuracion de infraestructura."
        ),
    }
