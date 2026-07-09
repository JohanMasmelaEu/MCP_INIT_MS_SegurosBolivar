FROM python:3.12-slim

LABEL maintainer="Equipo Arquitectura - Seguros Bolivar"
LABEL description="MCP Server para inicializacion de microservicios Java/Spring Boot"

WORKDIR /app

# Dependencias del sistema (git para validaciones futuras)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo fuente del MCP
COPY src/ ./src/

# Templates Jinja2 del arquetipo
COPY templates/ ./templates/

# Blueprints y rules transversales
COPY blueprints/ ./blueprints/
COPY rules/ ./rules/

# El workspace del usuario se monta en /workspace
VOLUME ["/workspace"]

ENV PYTHONUNBUFFERED=1
ENV MCP_WORKSPACE_PATH=/workspace

ENTRYPOINT ["python", "-m", "src.server"]
