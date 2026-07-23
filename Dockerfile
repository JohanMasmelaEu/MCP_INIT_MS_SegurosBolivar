FROM python:3.12-slim

LABEL maintainer="Equipo Arquitectura - Seguros Bolivar"
LABEL description="MCP Server para inicializacion de microservicios Java/Spring Boot"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY templates/ ./templates/
COPY blueprints/ ./blueprints/
COPY rules/ ./rules/

VOLUME ["/repos"]
VOLUME ["/settings"]

ENV PYTHONUNBUFFERED=1

EXPOSE 9752

ENTRYPOINT ["python", "-m", "src.server"]
