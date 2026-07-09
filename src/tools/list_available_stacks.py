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
                "description": (
                    "Microservicio Java con Spring Boot 4, Gradle, Spring Data JPA (PostgreSQL), "
                    "Spring Security (pluggable), SpringDoc OpenAPI, Docker Compose local "
                    "(LocalStack SSM/S3/SQS + Mock OAuth + Datadog Agent no-forward), "
                    "CI/CD GitHub Actions con templates institucionales Seguros Bolivar."
                ),
                "version": "1.0.0",
            }
        ],
        "note": (
            "V1 soporta unicamente java-spring-boot. "
            "Stacks futuros: python-fastapi, node-express, node-fastify."
        ),
    }
