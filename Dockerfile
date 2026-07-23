# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL maintainer="Equipo Arquitectura - Seguros Bolivar"
LABEL description="MCP Server para inicializacion de microservicios Java/Spring Boot"

WORKDIR /app

# Dependencias del sistema (git para validaciones futuras)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN --network=host pip install --no-cache-dir -r requirements.txt

# Codigo fuente del MCP
COPY src/ ./src/

# Templates Jinja2 del arquetipo
COPY templates/ ./templates/

# Blueprints y rules transversales
COPY blueprints/ ./blueprints/
COPY rules/ ./rules/

# /repos: bind mount al directorio de repos del host (ej: C:/REPOS)
# Los proyectos generados se escriben aqui.
VOLUME ["/repos"]

# /settings: volumen nombrado para persistir configuracion entre sesiones
# (directorio de salida configurado, preferencias del usuario)
VOLUME ["/settings"]

ENV PYTHONUNBUFFERED=1

# Puerto del Archetype Visualizer UI
EXPOSE 9752

ENTRYPOINT ["python", "-m", "src.server"]
