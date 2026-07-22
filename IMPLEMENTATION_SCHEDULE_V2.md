# Schedule de Implementación V2 — Personalización de Proyecto

## Contexto

Después de generar un proyecto con el MCP, el usuario tuvo que hacer ~8 archivos de ajustes manuales porque:
1. Los puertos estaban hardcodeados y colisionaban con otro MS del mismo ecosistema
2. La auth strategy `machine-to-machine` generaba artefactos de OAuth que no aplican
3. El cache Redis se declaró pero no se integró end-to-end
4. Los servicios de LocalStack no eran configurables
5. Las rutas SSM no eran coherentes entre yamls y seed-ssm

Este schedule cierra esos gaps haciendo que el MCP pregunte lo necesario y genere correcto de primera.

---

## Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `src/models/project_config.py` | Nuevos campos: ports, localstack_services, openapi_base_path, cors, extra_public_paths |
| `src/tools/get_required_inputs.py` | Nuevas categorías/campos de preguntas |
| `src/generators/java_spring_boot.py` | Lógica condicional por auth_strategy y cache |
| `templates/java-spring-boot/infra/docker-compose.yml.j2` | Puertos dinámicos, Redis condicional, mock-oauth condicional |
| `templates/java-spring-boot/infra/seed-localstack-ssm.sh.j2` | Params dinámicos según cache y auth |
| `templates/java-spring-boot/infra/env.sample.j2` | Variables dinámicas según config |
| `templates/java-spring-boot/infra/Dockerfile.j2` | Sin DD env vars hardcodeados |
| `templates/java-spring-boot/resources/application.yaml.j2` | Bloques condicionales por auth/cache |
| `templates/java-spring-boot/resources/application-local.yaml.j2` | Puertos y bloques condicionales |
| `templates/java-spring-boot/resources/application-test.yaml.j2` | Bloques condicionales |
| `templates/java-spring-boot/gradle/build.gradle.j2` | Deps condicionales por auth/cache |
| `templates/java-spring-boot/src/config/security/SecurityConfig.java.j2` | Condicional por auth_strategy |
| `templates/java-spring-boot/infra/mock-oauth-config.json.j2` | Solo generar si auth=oauth2-resource-server |

---

## TAREAS

### TASK 1 — Actualizar ProjectConfig con nuevos campos

**Archivo:** `src/models/project_config.py`

**Agregar al modelo `ProjectConfig`:**

```python
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

# --- OpenAPI ---
openapi_base_path: str = Field(
    default="/swagger-ui.html",
    description="Path base para documentación OpenAPI.",
)

# --- CORS ---
cors_allow_credentials: bool = Field(
    default=True,
    description="allowCredentials en CORS. False para APIs M2M sin cookies.",
)

# --- Endpoints públicos adicionales (sin auth) ---
extra_public_paths: list[str] = Field(
    default_factory=list,
    description="Paths adicionales que no requieren autenticación (ej: /api/v1/auth/token).",
)
```

**Agregar al modelo `DatabaseConfig`:**

```python
# Las rutas SSM se derivan del ssm_prefix de forma consistente:
@property
def ssm_endpoint(self) -> str:
    prefix = self.ssm_prefix or "/app/dev"
    return f"{prefix}/database/endpoint"

@property
def ssm_dbname(self) -> str:
    prefix = self.ssm_prefix or "/app/dev"
    return f"{prefix}/database/dbname"

@property
def ssm_username(self) -> str:
    prefix = self.ssm_prefix or "/app/dev"
    return f"{prefix}/database/username"

@property
def ssm_password(self) -> str:
    prefix = self.ssm_prefix or "/app/dev"
    return f"{prefix}/database/password"
```

**Criterio de done:** `ProjectConfig` instancia con los nuevos campos en defaults sin error.

---

### TASK 2 — Actualizar get_required_inputs con nuevas preguntas

**Archivo:** `src/tools/get_required_inputs.py`

**Nueva categoría `_ports_category()`:**

```python
def _ports_category() -> dict:
    """Categoria: puertos locales."""
    return {
        "name": "ports",
        "label": "Puertos Locales",
        "description": (
            "Puertos para evitar colisiones si hay otros MS corriendo en la misma maquina. "
            "Si no se cambian, se usan los defaults."
        ),
        "fields": [
            {
                "key": "app_port",
                "label": "Puerto HTTP de la app",
                "type": "integer",
                "required": False,
                "default": 8080,
                "description": "Cambiar si otro MS ya usa 8080 (ej: 8081, 8082).",
            },
            {
                "key": "localstack_port",
                "label": "Puerto de LocalStack",
                "type": "integer",
                "required": False,
                "default": 4566,
                "description": "Cambiar si otro MS ya usa 4566 (ej: 4567, 4568).",
            },
            {
                "key": "redis_port",
                "label": "Puerto Redis local (solo si cache=redis)",
                "type": "integer",
                "required": False,
                "default": 6379,
                "description": "Cambiar si otro servicio ya usa 6379 (ej: 6380).",
            },
        ],
    }
```

**Nueva categoría `_localstack_category()`:**

```python
def _localstack_category() -> dict:
    """Categoria: servicios LocalStack."""
    return {
        "name": "localstack",
        "label": "Servicios AWS Simulados (LocalStack)",
        "fields": [
            {
                "key": "localstack_services",
                "label": "Servicios a habilitar",
                "type": "array",
                "required": False,
                "default": ["ssm"],
                "description": "Servicios AWS que LocalStack simulara.",
                "options": ["ssm", "secretsmanager", "s3", "sqs", "events"],
            },
        ],
    }
```

**Nueva categoría `_security_details_category()`:**

```python
def _security_details_category() -> dict:
    """Categoria: detalles de seguridad."""
    return {
        "name": "security_details",
        "label": "Configuracion de Seguridad",
        "description": "Detalles adicionales de seguridad que dependen de la auth_strategy elegida.",
        "fields": [
            {
                "key": "cors_allow_credentials",
                "label": "CORS allowCredentials",
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "False para APIs M2M sin cookies. True si hay frontend con sesion.",
            },
            {
                "key": "extra_public_paths",
                "label": "Endpoints publicos adicionales (sin auth)",
                "type": "array",
                "required": False,
                "default": [],
                "description": "Paths que no requieren token (ej: /api/v1/auth/token, /api/v1/health).",
                "example": ["/api/v1/auth/token", "/api/v1/conexion/**"],
            },
            {
                "key": "openapi_base_path",
                "label": "Path base OpenAPI/Swagger",
                "type": "string",
                "required": False,
                "default": "/swagger-ui.html",
                "description": "Path custom para la documentacion (ej: /srv-miapp-openapi).",
            },
        ],
    }
```

**Agregar las 3 nuevas categorías a la lista en `handle_get_required_inputs`:**

```python
"categories": [
    _project_identity_category(),
    _domain_modules_category(),
    _database_category(),
    _authentication_category(),
    _security_details_category(),     # NUEVA
    _integrations_category(),
    _observability_category(),
    _ports_category(),                # NUEVA
    _localstack_category(),           # NUEVA
    _artifactory_category(),
    _mcp_marketplace_category(),
    _project_metadata_category(),
],
```

**Criterio de done:** `handle_get_required_inputs("java-spring-boot")` retorna 12 categorías.

---

### TASK 3 — Hacer auth_strategy un cleanup completo en el generador

**Archivo:** `src/generators/java_spring_boot.py`

**Principio:** Si auth_strategy NO es `oauth2-resource-server`, NO se genera nada relacionado con OAuth. Si NO es `deferred`, se genera la implementación concreta. El generador debe ser **aditivo según la estrategia**, no generar todo y dejar basura.

**Cambios en métodos:**

**`_generate_security()`** — hacer condicional:
```python
def _generate_security(self) -> None:
    """Genera paquete config/security/ segun la auth_strategy."""
    pkg = self.config.base_package_path

    # Siempre generar el SecurityConfig (su contenido varía por template)
    self._render_write(
        "src/config/security/SecurityConfig.java.j2",
        f"src/main/java/{pkg}/config/security/SecurityConfig.java",
    )
    # Siempre: headers y error handlers
    self._render_write(
        "src/config/security/SecurityHeadersFilter.java.j2",
        f"src/main/java/{pkg}/config/security/SecurityHeadersFilter.java",
    )
    self._render_write(
        "src/config/security/ApiErrorAccessDeniedHandler.java.j2",
        f"src/main/java/{pkg}/config/security/ApiErrorAccessDeniedHandler.java",
    )
    self._render_write(
        "src/config/security/ApiErrorAuthenticationEntryPoint.java.j2",
        f"src/main/java/{pkg}/config/security/ApiErrorAuthenticationEntryPoint.java",
    )
```

**`_generate_infrastructure()`** — mock-oauth condicional:
```python
def _generate_infrastructure(self) -> None:
    """Genera archivos de infraestructura local."""
    self._render_write("infra/Dockerfile.j2", "development/docker-local-ms/Dockerfile")
    self._render_write("infra/docker-compose.yml.j2", "development/docker-local-ms/docker-compose.yml")
    self._render_write("infra/down.ps1.j2", "development/docker-local-ms/down.ps1")
    self._render_write("infra/down.sh.j2", "development/docker-local-ms/down.sh")
    self._render_write("infra/seed-localstack-ssm.sh.j2", "development/docker-local-ms/scripts/seed-localstack-ssm.sh")
    self._render_write("infra/env.sample.j2", "development/.env.sample")
    self._render_write("infra/env.j2", ".env")

    # Mock OAuth solo si la estrategia lo requiere
    if self.config.auth_strategy.value == "oauth2-resource-server":
        self._render_write(
            "infra/mock-oauth-config.json.j2",
            "development/docker-local-ms/config/mock-oauth-config.json",
        )
```

**`_build_context()`** — agregar nuevos campos al contexto:
```python
# Agregar al diccionario retornado:
"app_port": self.config.app_port,
"localstack_port": self.config.localstack_port,
"redis_port": self.config.redis_port,
"localstack_services": self.config.localstack_services,
"cache": self.config.cache,
"openapi_base_path": self.config.openapi_base_path,
"cors_allow_credentials": self.config.cors_allow_credentials,
"extra_public_paths": self.config.extra_public_paths,
```

**Criterio de done:** Generar un proyecto con `auth_strategy: "machine-to-machine"` no produce mock-oauth-config.json ni dependencias OAuth.

---

### TASK 4 — Actualizar template docker-compose.yml.j2

**Archivo:** `templates/java-spring-boot/infra/docker-compose.yml.j2`

**Cambios:**

1. **Puertos dinámicos:** Reemplazar todo hardcoded `4566` por `{{ localstack_port }}`, `8080` por `{{ app_port }}`
2. **Redis condicional:**
```jinja2
{% if cache == "redis" %}
  redis:
    image: redis:7-alpine
    container_name: {{ c.project_name | replace('-', '-') }}-redis
    ports:
      - "{{ redis_port }}:6379"
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
{% endif %}
```

3. **Mock OAuth condicional:**
```jinja2
{% if auth_strategy == "oauth2-resource-server" %}
  mock-oauth:
    image: ghcr.io/navikt/mock-oauth2-server:2.1.10
    container_name: {{ c.project_name }}-mock-oauth
    ports:
      - "9411:9411"
    volumes:
      - ./config/mock-oauth-config.json:/config.json
    environment:
      - JSON_CONFIG_PATH=/config.json
{% endif %}
```

4. **LocalStack services dinámicos:**
```jinja2
  localstack:
    environment:
      - SERVICES={{ localstack_services | join(',') }}
```

5. **App environment — condicional por auth y cache:**
```jinja2
    environment:
      - SERVER_PORT=8080
      - AWS_SSM_ENDPOINT=http://localstack:4566
{% if auth_strategy == "oauth2-resource-server" %}
      - APP_AUTH_USE_API_GATEWAY=false
      - APP_OAUTH_COGNITO_DOMAIN=http://mock-oauth:9411
{% endif %}
{% if cache == "redis" %}
      - APP_REDIS_HOST=redis
      - APP_REDIS_PORT=6379
{% endif %}
```

6. **Depends_on condicional:**
```jinja2
    depends_on:
      localstack:
        condition: service_healthy
{% if cache == "redis" %}
      redis:
        condition: service_healthy
{% endif %}
{% if auth_strategy == "oauth2-resource-server" %}
      mock-oauth:
        condition: service_started
{% endif %}
```

**Criterio de done:** Template renderiza correctamente para los 4 auth strategies x con/sin redis (8 combinaciones).

---

### TASK 5 — Actualizar template build.gradle.j2

**Archivo:** `templates/java-spring-boot/gradle/build.gradle.j2`

**Cambios — dependencias condicionales:**

```jinja2
dependencies {
    // Core
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    implementation 'org.springframework.boot:spring-boot-starter-security'

{% if auth_strategy == "oauth2-resource-server" %}
    implementation 'org.springframework.boot:spring-boot-starter-oauth2-resource-server'
{% endif %}

{% if cache == "redis" %}
    implementation 'org.springframework.boot:spring-boot-starter-data-redis'
{% endif %}

    // WebClient para HTTP saliente
    implementation 'org.springframework.boot:spring-boot-starter-webflux'

    // ... (resto de deps fijas)

    // Testing
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.security:spring-security-test'
{% if auth_strategy == "oauth2-resource-server" %}
    testImplementation 'org.springframework.security:spring-security-oauth2-jose'
{% endif %}
}
```

**Cambios — bootRun environment condicional:**

```jinja2
bootRun {
    environment = [
        'SERVER_PORT'          : '{{ app_port }}',
        'AWS_SSM_ENDPOINT'     : 'http://localhost:{{ localstack_port }}',
        'AWS_REGION'           : 'us-east-1',
{% if auth_strategy == "oauth2-resource-server" %}
        'APP_OAUTH_COGNITO_DOMAIN': 'http://localhost:9411',
        'APP_AUTH_USE_API_GATEWAY': 'false',
{% endif %}
{% if cache == "redis" %}
        'APP_REDIS_HOST'       : 'localhost',
        'APP_REDIS_PORT'       : '{{ redis_port }}',
{% endif %}
    ]
}
```

**Criterio de done:** Build.gradle no incluye OAuth deps si auth != oauth2-resource-server. Incluye Redis si cache == redis.

---

### TASK 6 — Actualizar template application.yaml.j2

**Archivo:** `templates/java-spring-boot/resources/application.yaml.j2`

**Principio:** Solo incluir bloques de config que apliquen según auth_strategy y cache.

**Cambios clave:**

```jinja2
server:
  port: ${SERVER_PORT:{{ app_port }}}

spring:
  datasource:
    # ... (existente, sin cambio)

{% if cache == "redis" %}
  data:
    redis:
      host: ${APP_REDIS_HOST:localhost}
      port: ${APP_REDIS_PORT:{{ redis_port }}}
      timeout: 5000ms
{% endif %}

app:
  aws:
    ssm:
      endpoint: ${AWS_SSM_ENDPOINT:}
      region: ${AWS_REGION:us-east-1}
    db-params:
      endpoint: {{ c.database.ssm_endpoint }}
      dbname: {{ c.database.ssm_dbname }}
      username: {{ c.database.ssm_username }}
      password: {{ c.database.ssm_password }}
{% if cache == "redis" %}
    redis-params:
      host: {{ c.database.ssm_prefix }}/redis/host
      port: {{ c.database.ssm_prefix }}/redis/port
{% endif %}

{% if auth_strategy == "oauth2-resource-server" %}
  oauth:
    cognito:
      domain: ${APP_OAUTH_COGNITO_DOMAIN:}
      client-id: ${APP_OAUTH_CLIENT_ID:}
      client-secret: ${APP_OAUTH_CLIENT_SECRET:}
{% elif auth_strategy == "machine-to-machine" %}
  auth:
    jwt:
      signing-key: ${APP_JWT_SIGNING_KEY:}
      ttl-seconds: ${APP_JWT_TTL_SECONDS:3600}
    jwt-params:
      signing-key: {{ c.database.ssm_prefix }}/jwt/signing-key
      ttl-seconds: {{ c.database.ssm_prefix }}/jwt/ttl-seconds
{% endif %}

springdoc:
  api-docs:
    path: {{ openapi_base_path | default('/swagger-ui.html') }}
```

**Criterio de done:** Si auth=M2M, no hay bloque oauth. Si cache=none, no hay bloque redis. Rutas SSM coherentes con ssm_prefix.

---

### TASK 7 — Actualizar template application-local.yaml.j2

**Archivo:** `templates/java-spring-boot/resources/application-local.yaml.j2`

**Mismo principio:** Puertos dinámicos, bloques condicionales por auth/cache.

```jinja2
server:
  port: {{ app_port }}

{% if cache == "redis" %}
spring:
  data:
    redis:
      host: localhost
      port: {{ redis_port }}
{% endif %}

{% if auth_strategy == "oauth2-resource-server" %}
app:
  oauth:
    cognito:
      domain: http://localhost:9411
{% endif %}
```

**Criterio de done:** Perfil local solo contiene overrides relevantes según la config.

---

### TASK 8 — Actualizar template seed-localstack-ssm.sh.j2

**Archivo:** `templates/java-spring-boot/infra/seed-localstack-ssm.sh.j2`

**Cambios:**

```jinja2
#!/bin/bash
# Semilla de parametros SSM en LocalStack para {{ project_name }}
# Ejecutar despues de docker compose up (o automatico via healthcheck)

AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:{{ localstack_port }}}"
AWS_REGION="us-east-1"

put_param() {
  aws ssm put-parameter \
    --endpoint-url "$AWS_ENDPOINT_URL" \
    --region "$AWS_REGION" \
    --name "$1" --value "$2" --type String --overwrite 2>/dev/null
}

# Base de datos
put_param "{{ c.database.ssm_endpoint }}" "jdbc:postgresql://host.docker.internal:{{ c.database.db_port }}/{{ c.database.db_name }}"
put_param "{{ c.database.ssm_dbname }}" "{{ c.database.db_name }}"
put_param "{{ c.database.ssm_username }}" "{{ c.database.db_user }}"
put_param "{{ c.database.ssm_password }}" "{{ c.database.db_password }}"

{% if auth_strategy == "machine-to-machine" %}
# JWT
put_param "{{ c.database.ssm_prefix }}/jwt/signing-key" "local-dev-signing-key-do-not-use-in-prod"
put_param "{{ c.database.ssm_prefix }}/jwt/ttl-seconds" "3600"
{% endif %}

{% if cache == "redis" %}
# Redis
put_param "{{ c.database.ssm_prefix }}/redis/host" "redis"
put_param "{{ c.database.ssm_prefix }}/redis/port" "6379"
{% endif %}

echo "SSM parameters seeded OK ({{ project_name }})"
```

**Criterio de done:** Solo genera params que aplican según auth/cache. Usa ssm_prefix coherente.

---

### TASK 9 — Actualizar template SecurityConfig.java.j2

**Archivo:** `templates/java-spring-boot/src/config/security/SecurityConfig.java.j2`

**Principio:** El SecurityConfig se genera COMPLETO según la auth_strategy. No placeholder genérico.

```jinja2
{% if auth_strategy == "oauth2-resource-server" %}
    // OAuth2 Resource Server con JWT
    http.oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> {}));
{% elif auth_strategy == "machine-to-machine" %}
    // Machine-to-machine: JWT propio (agregar JwtAuthFilter)
    // TODO: Registrar JwtAuthFilter antes de UsernamePasswordAuthenticationFilter
{% elif auth_strategy == "api-gateway-delegated" %}
    // API Gateway valida el token — backend confía en headers del GW
{% else %}
    // Deferred: definir estrategia de auth
    // TODO: Implementar autenticacion
{% endif %}

    // Paths publicos
    http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/actuator/health", "/actuator/info").permitAll()
        .requestMatchers("{{ openapi_base_path }}/**").permitAll()
{% for path in extra_public_paths %}
        .requestMatchers("{{ path }}").permitAll()
{% endfor %}
        .anyRequest().authenticated()
    );

    // CORS
    http.cors(cors -> cors.configurationSource(request -> {
        var config = new org.springframework.web.cors.CorsConfiguration();
        config.setAllowCredentials({{ cors_allow_credentials | lower }});
        // ...
        return config;
    }));
```

**Criterio de done:** Cada auth_strategy produce un SecurityConfig coherente y funcional sin artefactos de otras estrategias.

---

### TASK 10 — Actualizar template Dockerfile.j2

**Archivo:** `templates/java-spring-boot/infra/Dockerfile.j2`

**Cambios:**
- Eliminar `ENV DD_AGENT_HOST=datadog-agent` (lo inyecta compose)
- Eliminar `ENV DD_TRACE_AGENT_PORT=8126` (lo inyecta compose)
- Agregar comentario: `# Container expone 8080 internamente. El host mapea a {{ app_port }}:8080`

**Criterio de done:** Dockerfile no tiene DD env vars hardcodeados.

---

### TASK 11 — Actualizar template env.sample.j2

**Archivo:** `templates/java-spring-boot/infra/env.sample.j2`

**Cambios — secciones condicionales:**

```jinja2
# === Artifactory ===
ARTIFACTORY_USER=
ARTIFACTORY_PASSWORD=

# === Aplicacion ===
SERVER_PORT={{ app_port }}
AWS_SSM_ENDPOINT=http://localhost:{{ localstack_port }}

{% if auth_strategy == "oauth2-resource-server" %}
# === OAuth (solo para bootRun en host, compose lo inyecta) ===
APP_OAUTH_COGNITO_DOMAIN=http://localhost:9411
APP_OAUTH_CLIENT_ID=local-client
APP_OAUTH_CLIENT_SECRET=local-secret
APP_AUTH_USE_API_GATEWAY=false
{% elif auth_strategy == "machine-to-machine" %}
# === JWT (solo para bootRun en host) ===
APP_JWT_SIGNING_KEY=local-dev-signing-key-do-not-use-in-prod
APP_JWT_TTL_SECONDS=3600
{% endif %}

{% if cache == "redis" %}
# === Redis (solo para bootRun en host) ===
APP_REDIS_HOST=localhost
APP_REDIS_PORT={{ redis_port }}
{% endif %}

# Nota: En Docker compose, todas estas variables se inyectan automaticamente.
# Este archivo es solo para ejecutar con ./gradlew bootRun en el host.
```

**Criterio de done:** Solo muestra variables relevantes según auth/cache.

---

### TASK 12 — Actualizar _flatten_categorized_config para nuevos campos

**Archivo:** `src/server.py`

**En `_flatten_categorized_config()`**, agregar manejo para las nuevas categorías:

```python
# ports → campos planos
if "ports" in config_dict:
    flat.update(config_dict["ports"])

# localstack → extraer localstack_services
if "localstack" in config_dict:
    ls = config_dict["localstack"]
    if isinstance(ls, dict) and "localstack_services" in ls:
        flat["localstack_services"] = ls["localstack_services"]

# security_details → campos planos
if "security_details" in config_dict:
    flat.update(config_dict["security_details"])
```

**Criterio de done:** Input categorizado con ports/localstack/security_details se aplana correctamente.

---

### TASK 13 — Actualizar get_project_plan para reflejar condicionales

**Archivo:** `src/tools/get_project_plan.py`

**En `_build_file_tree()`**, hacer condicional la generación de mock-oauth:

```python
# --- Infraestructura ---
# ... (existente)

# Mock OAuth solo si aplica
if config.auth_strategy.value == "oauth2-resource-server":
    files.append(
        _file(f"{p}/development/docker-local-ms/config/mock-oauth-config.json", "Config Mock OAuth Server")
    )
```

**En `_build_decisions()`**, agregar info de puertos y cache:

```python
decisions.append(f"Puertos: app={config.app_port}, LocalStack={config.localstack_port}")
if config.cache:
    decisions.append(f"Cache: {config.cache} (puerto {config.redis_port})")
else:
    decisions.append("Cache: ninguno")
decisions.append(f"LocalStack services: {', '.join(config.localstack_services)}")
```

**Criterio de done:** Plan muestra puertos, cache, y no incluye mock-oauth si no aplica.

---

### TASK 14 — Verificar coherencia end-to-end

**Prueba manual:**

Generar un proyecto con esta config y verificar que no requiere ajustes manuales:

```json
{
  "project_name": "test-m2m-redis-ms",
  "context_path": "/test_m2m",
  "api_description": "Test M2M con Redis",
  "database": {"db_name": "test_db", "db_user": "user", "db_password": "pass", "db_port": 5433, "ssm_prefix": "/test/dev"},
  "auth_strategy": "machine-to-machine",
  "cache": "redis",
  "app_port": 8081,
  "localstack_port": 4567,
  "redis_port": 6380,
  "localstack_services": ["ssm", "secretsmanager"],
  "cors_allow_credentials": false,
  "extra_public_paths": ["/api/v1/auth/token"],
  "openapi_base_path": "/srv-test-openapi",
  "modules": [{"module_name": "clientes", "entity_name": "Cliente", "table_name": "CLIENTE", "fields": []}]
}
```

**Verificar:**
- [ ] docker-compose.yml: no tiene mock-oauth, sí tiene redis en 6380, app en 8081, localstack en 4567
- [ ] build.gradle: no tiene oauth2-resource-server dep, sí tiene data-redis
- [ ] application.yaml: no tiene bloque oauth, sí tiene bloque redis y jwt
- [ ] seed-ssm: tiene params DB + JWT + Redis, no tiene params OAuth
- [ ] SecurityConfig: no tiene oauth2ResourceServer(), sí tiene JWT TODO y extra_public_paths
- [ ] .env.sample: solo variables JWT y Redis, no OAuth
- [ ] Dockerfile: sin DD env vars
- [ ] mock-oauth-config.json: NO existe

---

## NOTAS PARA EL AGENTE EJECUTOR

1. **Los templates Jinja2 usan `{% if auth_strategy == "..." %}` directamente** — la variable `auth_strategy` es un string en el contexto del template (se pasa con `.value` desde el enum).

2. **El cache se compara como `{% if cache == "redis" %}` o `{% if cache %}`** — si es None/empty string, el bloque no se genera.

3. **No eliminar los templates existentes de OAuth** — solo envolverlos en condicionales `{% if auth_strategy == "oauth2-resource-server" %}`.

4. **Los puertos en docker-compose tienen mapeo host:container** — el container siempre ve 8080 internamente, el host mapea a `{{ app_port }}:8080`.

5. **Las rutas SSM deben ser coherentes** — usar siempre las propiedades computadas de DatabaseConfig (`ssm_endpoint`, `ssm_dbname`, etc.) derivadas de `ssm_prefix`.

6. **Si el usuario no responde nada sobre cache, puertos, localstack_services, etc.** — se usan los defaults. El proyecto debe funcionar con TODOS los defaults sin ninguna pregunta extra respondida.
