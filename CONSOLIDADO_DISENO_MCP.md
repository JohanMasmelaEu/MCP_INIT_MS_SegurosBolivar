# Consolidado Final — MCP_INIT_MS_SegurosBolivar

## 1. Visión

Este MCP genera **proyectos backend (microservicios)** con un workspace Kiro inteligente que:

- Enseña las convenciones mientras el desarrollador trabaja (steering)
- No permite uso irresponsable del agente (hooks de validación)
- Exige calidad sin ser autoritario — override con confirmación tácita
- Obliga al agente a ceñirse a la arquitectura suministrada, sin inventar ni divergir
- Funciona igual sin importar el stack backend (Java, Python, Node)
- Es modular y extensible

**Alcance:** Solo backend. Frontend, base de datos y Postman Collections tendrán MCPs dedicados en el futuro.

---

## 2. Principios Transversales

### 2.1 Confirmación con contexto

Ninguna regla bloquea sin dar opción. Flujo:

1. Detectar el problema
2. Informar QUÉ encontró y POR QUÉ es un riesgo
3. Preguntar: "¿Deseas proceder así?"
4. Si confirma → procede (decisión consciente)
5. Si no → ayudar a corregir

**Excepciones absolutas (sin override):**

- Secrets/credenciales hardcoded en código
- SQL concatenado con input de usuario sin parametrizar

### 2.2 Stack-agnostic

Lo organizacional y de calidad aplica sin importar la tecnología. Solo las herramientas concretas cambian por stack.

### 2.3 El agente es un copiloto, no un autopiloto

El usuario siempre debe entender, validar y ser responsable de lo que se implementa.

### 2.4 Adherencia absoluta a la arquitectura

- **Para el agente:** la arquitectura es LEY. Nunca la rompe por su cuenta.
- **Para el usuario:** puede decidir romperla, pero el agente le informa qué está por hacer y el riesgo. Si confirma, procede.

La arquitectura es una restricción del agente, no del humano. El humano siempre tiene la última palabra con plena consciencia.

### 2.5 Plan siempre existe — varía la profundidad

Todo cambio va precedido de un plan. Lo que varía es el nivel de profundidad y si requiere confirmación, determinado por criterios objetivos, no por juicio del agente.

- **Plan ligero (default, todo cambio):** 1-2 líneas declarando qué se va a hacer, antes de ejecutar. No bloquea, no espera confirmación.
- **Plan completo (solo si activa el gate):** desglose paso a paso (archivos, impacto, riesgos) + espera confirmación explícita.

El nivel lo determina el hook, no el criterio del agente.

---

## 3. Estructura generada por el MCP

```
proyecto-generado/
├── .kiro/
│   ├── project.json                   ← metadato: stack, generatedBy, createdAt
│   ├── steering/
│   │   ├── 00-org-conventions.md
│   │   ├── 01-architecture.md
│   │   ├── 02-security.md
│   │   ├── 03-code-style.md
│   │   ├── 04-testing-standards.md
│   │   ├── 05-responsible-ai-use.md
│   │   ├── 06-data-access.md
│   │   ├── 07-error-handling.md
│   │   ├── 08-observability.md
│   │   ├── 10-stack-java.md              ← condicional (project.json.stack == java)
│   │   ├── 10-stack-python.md            ← condicional (project.json.stack == python)
│   │   ├── 10-stack-node.md              ← condicional (project.json.stack == node)
│   │   ├── 90-legacy-oracle.md           ← manual/situacional
│   │   └── 91-legacy-soap.md             ← manual/situacional
│   └── hooks/
│       ├── pre-write-gate.json            ← consolidado: plan + arquitectura + calidad
│       ├── responsible-use.json
│       ├── code-review-gate.json
│       ├── test-coverage-gate.json
│       ├── build-validate.json
│       ├── integrity-check.json           ← SessionStart: verifica hooks activos
│       └── summary-on-completion.json
├── src/...
└── ...
```

**Metadato del proyecto (`.kiro/project.json`):**

```json
{
  "stack": "java",
  "dockerProfile": "java-redis",
  "cache": "redis",
  "i18n": ["es", "en"],
  "generatedBy": "mcp-init-ms-segurosbolivar",
  "createdAt": "2026-07-16"
}
```

`dockerProfile`, `cache` e `i18n` se responden en el mismo flujo de inputs del MCP al inicializar (no son decisiones posteriores en runtime). El stack, y el resto de metadatos, se definen una única vez al inicializar vía MCP. Los steerings condicionales (`10-stack-*.md`) se activan leyendo ese campo, no por fileMatch de extensión.

---

## 4. Detalle de Steering Files

### `00-org-conventions.md` — Convenciones Organizacionales

**Inclusión:** Always

#### URLs — Estructura de nombramiento

```
host:port/[dominio]/[capa]/[version]/[funcionalidad]/[entidad]
```

| Etiqueta | Definición |
|----------|-----------|
| Dominio | Dominio de negocio del microservicio |
| Capa | `api` (implementación), `composición` (orquestación de varios dominios), `lambda` (transformación con Colas/Steps Functions) |
| Versión | Prefijo "v", enteros: v1, v2...vx. Nunca decimales |
| Funcionalidad | Lugar donde se modifica el objeto/entidad (opcional) |
| Entidad | Objeto que detalla la acción, en plural. Puede tener niveles de especialización |

#### Verbos HTTP

| Verbo | Uso |
|-------|-----|
| GET | Consultar recursos (solo parámetros, nunca body) |
| POST | Crear recursos o ejecutar operaciones (parámetros y/o requestBody) |
| PUT | Actualizar recurso completo (parámetros y/o requestBody) |
| PATCH | Actualizar parcial de un recurso (parámetros y/o requestBody) |
| DELETE | Eliminar recursos (solo parámetros) |
| OPTIONS | Preflight CORS / descubrir métodos permitidos en un recurso |

#### Naming de objetos

| Objeto | Convención | Ejemplo |
|--------|-----------|---------|
| Controller | Nombre operación + "Controller" | `TerceroConsultableController` |
| Service (interface) | Nombre operación + "Service" | `TerceroConsultableService` |
| Service (impl) | Nombre operación + "ServiceImpl" | `TerceroConsultableServiceImpl` |
| Request | Nombre operación + "Request" | `TerceroActualizarRequest` |
| Response | Nombre operación + "Response" | `TerceroActualizarResponse` |
| Repository (función) | "Fun" + nombre PL + "Repository" | `FunValidaCiudadRepository` |
| Repository (procedure) | "Prc" + nombre PL + "Repository" | `PrcGenerarCertificadoRepository` |
| Paquete operación | Funcionalidad en infinitivo + plural, minúscula, sin caracteres especiales | `consultarterceros` |

#### Idioma

- Inglés por defecto
- Español permitido en: nombres de objetos, nombres de métodos, paquete principal de operación, comentarios, documentación README y Swagger

#### Lineamientos generales

- Máximo 15 operaciones por microservicio
- Una URL identifica un recurso
- Sustantivos en plural solamente
- Verbos HTTP apropiados según funcionalidad
- Formato de respuesta: JSON (Content-Type: application/json; charset=utf-8)
- Campos opcionales como lista separada por comas

#### Documentación — README principal

Nombre del repositorio, resumen de funcionalidades, tags, tabla de contenido, descripción, detalle de funcionalidades (lista con link al README de cada operación), arquitectura, construido con, desarrollo (instructivo local), seguridad, endpoints (DEV/STAGE/PROD), licencia.

#### Documentación — README por operación

Título, resumen, tags, tabla de contenido, descripción (servicios que consume), detalle (verbo HTTP + path + tabla headers + request + response OK + response ERROR + notas), proyectos relacionados, endpoints por ambiente, apikeys, autores (equipo, líder técnico, arquitecto), licencia.

#### Backward compatibility

- Ventana de deprecación default: 90 días desde que se marca deprecated hasta el sunset. Ajustable por el usuario según el caso.
- Marcado: header `Deprecation: true` + `Sunset: <fecha ISO>` en la versión vieja, más entrada en el changelog.
- Crear v2 no marca v1 como deprecated automáticamente — es decisión explícita y separada del usuario.
- Rollback: dentro de la ventana de deprecación, v1 sigue operativa sin acción extra. Post-sunset, rollback vía tag de repo.

> Nota: este criterio se establece como punto de partida razonable, con apertura a ajuste cuando haya más contexto de uso real.

#### Internacionalización (i18n) de mensajes

- Default: mensajes (errores, validaciones, respuestas) en **español**.
- Si el usuario habilita inglés (`project.json.i18n: ["es","en"]`), se homologa lo existente en español y, desde ese momento, todo mensaje nuevo se genera en **ambos idiomas activos simultáneamente** — nunca se agrega uno sin el otro si ambos están habilitados.
- Los idiomas activos viven en `project.json.i18n`; el agente consulta ese arreglo para saber cuántas variantes generar.

#### Contenerización — ownership

- El Dockerfile **no se genera en este repo**. Vive en un repo dedicado, sin valores quemados, y consume el package/artifact generado aquí, indexado según `project.json.dockerProfile`.
- El perfil de imagen (stack + si incluye cache/Redis) se define en el mismo flujo de inicialización del MCP y queda registrado en `project.json.dockerProfile`.
- La imagen ya sabe qué crear/ajustar según las variables definidas en `.env` del proyecto generado.

#### Cache (Redis) — opcional

- Redis es seleccionable al inicializar el proyecto (`project.json.cache`). Si se activa, la imagen Docker indexada lo incluye.
- En local, se simula con LocalStack (o equivalente) replicando el comportamiento de un ambiente ya desplegado.

#### Configuración por ambiente

- Nombrado sigue convención estándar de industria (`application-{profile}.yml`, `.env.{env}`).
- Alcance limitado a lo que el desarrollador necesita en local. Los valores reales de despliegue (Dev/Stage/Prod) son responsabilidad del repo `-infra` vía Terraform — este MCP no los gestiona.

#### Postman Collections — ownership

- Este MCP no genera ni mantiene `postmanCollections/`.
- Dicha responsabilidad corresponde a un MCP dedicado (futuro), que generará las colecciones a partir del contrato exportable (OpenAPI/JSON Schema) que este MCP sí produce.
- Sigue siendo obligatorio a nivel de estándar del proyecto — se reubica de owner, no se elimina.

---

### `01-architecture.md` — Arquitectura Backend

**Inclusión:** Always

**Alcance:** Este proyecto es un microservicio backend. Frontend y base de datos son responsabilidad de otros repos/MCPs.

#### Estructura del código — Organización por dominio de negocio

Sencillo, ordenado, y preparado para crecer sin reescribir.

- Hoy puede tener un solo dominio → funciona limpio
- Mañana se agregan más dominios → cada uno en su carpeta, sin pisar los demás
- No es DDD formal (no requiere agregados, domain events, value objects)
- Es: cada funcionalidad de negocio vive junta y separada de las demás

```
com.bolivar.<artifact>/
├── Application.java
├── config/              ← configuración general del MS
├── commons/             ← objetos compartidos entre dominios (si aplica)
├── errorhandling/       ← manejo global de excepciones
├── utils/               ← utilidades transversales
└── <dominio>/           ← un dominio por carpeta
    ├── controller/
    ├── dto/
    ├── services/        (interface + impl)
    └── repository/
```

Agregar un nuevo dominio:

```
└── <nuevo-dominio>/     ← se agrega sin tocar los existentes
    ├── controller/
    ├── dto/
    ├── services/
    └── repository/
```

#### Reglas de estructura

- NO agrupar por tipo técnico (no "todos los controllers juntos")
- SI agrupar por funcionalidad de negocio
- Cada dominio es independiente, no depende directamente de otros
- Va a `commons/` si: (1) lo usa más de 1 dominio, o (2) el usuario lo declara desde el inicio como transversal. En el caso (2), el agente debe informar explícitamente: *"Este espacio es para herramientas/componentes transversales — ¿confirmas que aplica aquí?"* — decisión consciente, no automática ni a juicio libre del agente.

#### Contrato entre dominios

- Cada dominio expone un único punto de entrada público (su API pública)
- Lo interno (repository, servicios internos, entities) es privado — no importable desde otro dominio
- Comunicación directa y síncrona entre dominios vía su punto de entrada público (sin eventos por ahora)
- Dependencias unidireccionales (jerarquía explícita, validada por linter)
- Si mañana se extrae un dominio a su propio despliegue, solo cambia el transporte — la forma se mantiene

#### Resiliencia

- Circuit breakers en llamadas externas
- Async para operaciones pesadas (retornar 202 + job ID)
- Fail-fast con timeouts bajos para transacciones cortas
- Rate limiting para proteger componentes core

#### Concurrencia y transacciones (nivel básico)

- POST que crea recursos: debe soportar `Idempotency-Key` o validar clave natural antes de insertar (evitar duplicados en reintentos)
- Entidades propensas a edición concurrente: incluir campo `version`, UPDATE condicionado a esa versión (409 si no coincide)
- Escrituras multi-tabla dentro de un mismo dominio: siempre en transacción nativa del ORM
- Escrituras cross-dominio: no se fuerza transacción distribuida; se documenta como consistencia eventual o se resuelve por orden de operaciones
- Fuera de alcance: Saga, 2PC, orquestadores, locks distribuidos

#### API First

- OpenAPI spec como source of truth
- Versionamiento en URL
- Backward compatibility durante deprecación (ver sección en `00-org-conventions.md`)
- Contratos exportables (OpenAPI, JSON Schema) para no bloquear futura integración con otros MCPs

#### Ownership de schema y migraciones

- El repo de backend define entities como modelo de dominio en código, pero NO genera ni ejecuta migraciones (no incluye Flyway/Liquibase/Alembic)
- Todo cambio de entity que implique cambio de schema se declara explícitamente en el plan como "requiere migración en repo de DB", sin ejecutarlo
- El traslado de la propuesta al repo de DB es una decisión manual del usuario
- El MCP de DB (futuro) es el único que genera y aplica migraciones

#### Governance

- Dependencias exclusivamente de JFrog Artifactory
- Ambientes separados (Dev, Stage, Prod)
- Graceful shutdown
- Solo stack tecnológico aprobado

#### Connection pooling (DB)

- Tamaño de pool y timeouts se leen de variable de entorno al declarar la conexión backend-DB.
- Gestionable por infra vía Parameter Store/Secret Manager. Si no está definida, aplica un valor default declarado en el steering del stack correspondiente.
- El arquitecto define el rango permitido; el desarrollador ajusta el valor dentro de ese rango vía la variable de entorno.

#### File upload / multipart

- No hay estándar genérico del MCP para esto. Es decisión de arquitectura por proyecto: el arquitecto define si aplica carga de archivos, qué tipos se permiten y dónde se almacenan.

---

### `02-security.md` — Seguridad

**Inclusión:** Always

#### Input — Zero Trust

- Todo input es malicioso hasta validado
- Validar tipo, formato, longitud, rango, enum, presencia en servidor SIEMPRE
- Normalizar inputs (trim, unicode)
- Limitar body, header, query param, file sizes
- Rechazar keys inesperadas
- Formatos estrictos (UUID v4, ISO-8601)

#### Inyección

- Prepared statements / queries parametrizadas SIEMPRE
- Nunca concatenar strings para SQL
- En ORMs, nunca `.raw()` con input sin sanitizar
- Para NoSQL, allowlist de campos filtrables
- Nunca `exec("cmd " + userInput)` ni `shell=True`

#### SSRF

Allowlist de dominios, bloquear IPs privadas, HTTPS only, timeouts estrictos.

#### Path Traversal

Canonicalizar con realpath, verificar directorio permitido, bloquear "..".

#### Auth

Tokens short-lived + refresh rotation, cookies Secure + HttpOnly + SameSite, rate limit + lockouts.

#### BOLA/IDOR

Verificar permisos en cada request, nunca confiar en IDs del cliente, verificación explícita owner/tenant/org.

#### Headers obligatorios

HSTS, CSP, X-Content-Type-Options: nosniff, X-Frame-Options, Referrer-Policy, Permissions-Policy. Forzar HTTPS.

#### Secrets

Nunca en código. Via Secret Manager o env vars. Comunicación por DNS.

#### Information Leakage

- No PII/secrets en logs, traces, errors, analytics
- Responses con DTOs allowlisted, nunca objetos completos
- Masking de campos sensibles (`****1234`)
- Nunca stack traces al cliente

#### Dependencias

Pinned exact versions. Auditar en pipeline. Generar SBOM.

---

### `03-code-style.md` — Código Limpio

**Inclusión:** Always

#### Principios

DRY, SOLID, KISS. Código legible primero.

#### Funciones

Max ~20 líneas. Single purpose. Max 3 params. Complejidad ciclomática max 15.

#### Type safety

Type hints/strict types obligatorios. Nunca `any`, `Object`, `dict` sin tipo.

#### Naming

Descriptivo. Booleans: `isActive`/`hasPermission`. Clases PascalCase. Métodos/variables camelCase (Java/Node) o snake_case (Python). Constantes UPPER_SNAKE_CASE.

#### Imports

Orden: stdlib → third-party → local. Específicos. Sin circulares.

#### Dead code

Cero. Git es el historial.

#### Documentación

Docstring/Javadoc en todo método público no trivial.

#### SonarQube

Min 80% coverage. Zero critical/blocker. Complejidad max 15.

#### Trash to Delete Trash — Definición de código basura

| Severidad | Qué es |
|-----------|--------|
| **Bloquea (sin override)** | Secrets hardcoded, SQL concatenado con user input |
| **Requiere justificación** | TODO/FIXME sin resolver, código commented-out, métodos > 30 líneas, duplicación, System.out/console.log/print de debug, catch vacíos |
| **Recomendación** | Imports no usados, variables sin uso, comentarios redundantes, métodos privados no llamados |

**Trash Inspector:** Herramienta auxiliar (no gate bloqueante). Se sugiere al usuario ejecutarlo al terminar una funcionalidad. El usuario decide si la usa. Cuando se ejecuta, muestra hallazgos y recomendaciones sin bloquear.

---

### `04-testing-standards.md` — Testing

**Inclusión:** Always

| Regla | Detalle |
|-------|---------|
| Coverage | Mínimo 80%. Build FALLA si < 80% |
| Patrón | Given/When/Then (Arrange/Act/Assert) |
| Mocks | Obligatorio para dependencias externas. Nunca backends reales |
| Error paths | Tests DEBEN cubrir caminos de error |
| Completitud | Toda feature/fix lleva tests. Tarea no está completa sin tests |
| Exclusiones | test, models/dto, repository interfaces, config, utils, messages |

**Por stack:**

| Stack | Framework | Coverage tool |
|-------|-----------|--------------|
| Java | JUnit 5 + Mockito + WireMock | JaCoCo |
| Python | pytest + httpx | pytest-cov |
| Node | Jest + Supertest | jest --coverage |

---

### `05-responsible-ai-use.md` — Uso Responsable de IA

**Inclusión:** Always

#### Plan — dos niveles

Todo cambio va precedido de un plan. El nivel lo determina el hook, no el criterio del agente.

- **Plan ligero (default):** 1-2 líneas declarando qué se va a hacer. No bloquea.
- **Plan completo (si activa gate):** paso a paso + confirmación explícita.

**Criterio determinístico para escalar a plan completo (OR):**

| Condición | Dispara plan completo |
|-----------|----------------------|
| Diff > 15 líneas | Sí |
| Más de 1 archivo tocado | Sí |
| Toca `dto/`, `schema/`, `*.model.*`, `config/`, `auth/` | Sí (aunque sea 1 línea) |
| Fuera de lo anterior | No — solo plan ligero |

#### Validación de prompt

- No evaluar por longitud del prompt
- Verificar si contiene: (a) acción reconocible + (b) objeto/entidad concreto
- Si ambos presentes → proceder sin preguntar, sin importar brevedad
- Si falta alguno → preguntar específicamente qué falta, no pedir "elaborar más" genérico

#### Post-implementación

Resumen de lo hecho + pedir validación del usuario.

#### Override

Todas las reglas permiten override con confirmación tácita. Excepto: secrets hardcoded y SQL injection.

#### ADHERENCIA ABSOLUTA A LA ARQUITECTURA

| Prohibido (para el agente) | Permitido |
|-----------|-----------|
| Sugerir cambios de arquitectura no solicitados | Preguntar si detecta inconsistencia legítima |
| Inventar funcionalidades fuera del scope | Preguntar si cree que algo falta |
| Presentar alternativas como "la única opción" | Explicar limitación técnica + alternativa cercana |
| Refactorizar código no pedido | Implementar exactamente lo solicitado |
| Agregar features "bonus" | Ceñirse al scope definido |
| Insistir tras rechazo del usuario | Buscar la forma de cumplir lo pedido |
| Tomar el camino conveniente para el agente | Tomar el camino definido por el proyecto |
| Decirle al usuario que "hable con arquitectura" | Implementar dentro del marco existente |

**Si no puede implementar exactamente lo pedido:**

1. Explicar POR QUÉ (técnicamente)
2. Alternativa más cercana
3. ESPERAR confirmación
4. Si el usuario insiste → buscar la forma

**Si detecta inconsistencia:**

> "Veo que el patrón actual usa X pero me pides Y. ¿Implemento Y como pides, o sigo el patrón existente?"

**La arquitectura es LEY para el agente.** El usuario puede decidir romperla — pero el agente informa el riesgo y espera confirmación. Nunca decide por el usuario.

#### AI-generated code

Se trata como untrusted. Validar lógica, seguridad, alignment con patrones antes de integrar. Verificar dependencias sugeridas en registry oficial y JFrog.

---

### `06-data-access.md` — Acceso a Datos

**Inclusión:** Always

#### ORM obligatorio

| Stack | ORM | Alternativa aprobada |
|-------|-----|---------------------|
| Java | Spring Data JPA + Specification | JPQL con @Query parametrizado |
| Python | SQLAlchemy 2.x | Tortoise ORM |
| Node | pg con query parametrizado | - |

#### Prohibido (salvo confirmación explícita del usuario)

- String concatenation para SQL
- Queries dentro de loops (N+1)
- `.findAll()` sin paginación
- Consultas cíclicas
- Scripts SQL como strings

#### Obligatorio

- Repositories tipados con métodos declarativos
- Specification/filtros dinámicos
- Paginación SIEMPRE en listados
- JOIN FETCH para evitar N+1
- Índices documentados
- Queries parametrizados si SQL custom

#### SQL raw — escape hatch

Solo con confirmación explícita del usuario + justificación + SIEMPRE parametrizado. El agente debe preguntar primero si puede resolverse con el ORM.

---

### `07-error-handling.md` — Manejo de Excepciones

**Inclusión:** Always

#### Principio

Un HTTP 500 es un bug. Toda excepción previsible debe capturarse y traducirse a un error con código y HTTP status apropiado.

#### Obligatorio

- GlobalExceptionHandler (retorna error genérico, nunca stack trace)
- Validación de entrada con framework del stack ANTES de la lógica
- Excepciones de negocio custom con código semántico + HTTP status apropiado (400, 404, 409, 422)
- Tests de caminos de error

#### Prohibido

- `catch(Exception) { return null; }`
- Stack traces al cliente
- Dejar NullPointer/ClassCast/NumberFormat propagarse como 500
- Asumir input siempre correcto

#### Formato error

```json
{"codigo": "CODIGO_ERROR", "mensaje": "Descripción legible", "data": null}
```

#### Capas

| Capa | Maneja |
|------|--------|
| Controller | Binding/parsing de entrada |
| Service | Lógica → excepciones custom |
| Repository | Errores BD → excepciones del dominio |
| Global Handler | Red de seguridad final |

---

### `08-observability.md` — Observabilidad

**Inclusión:** Always

> **Nota de alcance:** Este documento aplica a la plantilla Java/Spring. Para Python/FastAPI y Node/Express, se definirá un steering equivalente al crear esas plantillas, siguiendo el mismo contrato (health check, logs estructurados, métricas) con herramientas nativas de cada stack.

#### Por ambiente

| Ambiente | Nivel | Formato | Masking | Detalle |
|----------|-------|---------|---------|---------|
| **Local** | DEBUG | Consola legible | OFF | Payloads completos, stack traces, queries |
| **Productivo** | INFO | JSON estructurado | ON | Campos sensibles ofuscados, correlation-ID |
| **Soporte** | Dinámico (Actuator) | JSON | ON | Tramas en Datadog con permisos, sin redespliegue |

#### Correlation ID

- Obligatorio en toda request
- Se lee de `X-Correlation-ID` o se genera UUID si no viene
- Se inyecta en MDC/context
- Se propaga a downstream

#### Masking (solo prod)

Campos: documento, numeroTarjeta, password, token, email, telefono → `****XXXX`.
Configuración por perfil: OFF en local, ON en prod.

#### Niveles

- ERROR: fallo que requiere atención
- WARN: anómala recuperable
- INFO: eventos de negocio
- DEBUG: detalle técnico (solo local o temporal via Actuator)

#### Prohibido

Loguear passwords/tokens/secrets (ni en local). Stack traces al cliente. Logs sin correlation_id.

#### Contrato cross-stack (principio general)

Todo servicio debe exponer: health check, logs estructurados, métricas. Cómo se logra es específico de cada plantilla.

---

### `10-stack-java.md` — Java/Spring Boot

**Inclusión:** Condicional (`project.json.stack == java`)

| Componente | Detalle |
|-----------|---------|
| Java | JDK 21 LTS |
| Gradle | 9.4.1 |
| Spring Boot | 4.0.2 |
| ORM | Spring Data JPA + JpaSpecificationExecutor |
| Validación | Jakarta Validation |
| Docs API | springdoc-openapi 3.0.2 |
| Testing | JUnit 5 + Mockito + WireMock + JaCoCo |
| Error handling | BolivarBusinessException + GlobalExceptionHandler |
| Logs | bolivar-centralizador-logs + Logback MDC |
| HTTP Client | WebClient (nunca OkHttp) |
| AWS | aws-java-sdk-ssm |
| Librerías internas | commons-gradle-error-handling-java, bolivar-centralizador-logs |

---

### `10-stack-python.md` — Python/FastAPI

**Inclusión:** Condicional (`project.json.stack == python`)

| Componente | Detalle |
|-----------|---------|
| Python | 3.12+ |
| Dep Manager | Poetry 1.8+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x + asyncpg |
| Validación | Pydantic v2 |
| Testing | pytest + httpx + coverage |
| HTTP Client | httpx async |
| Migraciones | No incluidas (ownership del MCP de DB) |

---

### `10-stack-node.md` — Node/Express

**Inclusión:** Condicional (`project.json.stack == node`)

| Componente | Detalle |
|-----------|---------|
| Node.js | 20.x LTS |
| npm | 10.x+ |
| Framework | Express / Fastify 4.x |
| BD | pg parametrizado |
| Validación | Zod / Joi |
| Seguridad | Helmet + CORS + Passport.js + JWT |
| Testing | Jest + Supertest + coverage |
| HTTP Client | axios |
| Migraciones | No incluidas (ownership del MCP de DB) |

---

### `90-legacy-oracle.md` — Legacy Oracle/MyBatis

**Inclusión:** Manual (el usuario lo activa cuando lo necesita)

**Cuándo aplica:** Proyecto requiere consumo de procedimientos almacenados Oracle, lógica en BD por directriz de arquitectura/negocio, coherencia con sistema legacy existente.

**Contenido:** Patrones MyBatis, naming Fun/Prc para repositories, handlers de STRUCT/ARRAY, librería MyBatis Bolívar (`commons-gradle-mybatisutils-local`), librería ParameterStore (`commons-gradle-parameter-store-local`).

---

### `91-legacy-soap.md` — Legacy SOAP/CXF

**Inclusión:** Manual

**Cuándo aplica:** Integración con servicios legacy SOAP.

**Contenido:** Apache CXF, generación de clientes WSDL, patrones de consumo.

---

## 5. Detalle de Hooks

### `pre-write-gate.json` — Gate consolidado pre-escritura

| Campo | Valor |
|-------|-------|
| **Trigger** | PreToolUse |
| **Matcher** | `fs_write\|str_replace\|fs_append` |
| **Tipo** | agent |
| **Filtro path** | Solo archivos en `src/` (excluye tests, docs, generados) |

**Lógica:**

Evalúa condiciones OR para decidir nivel de plan:

| Condición | Acción |
|-----------|--------|
| Diff > 15 líneas | Plan completo + confirmación |
| Más de 1 archivo tocado | Plan completo + confirmación |
| Toca `dto/`, `schema/`, `*.model.*`, `config/`, `auth/` | Plan completo + confirmación |
| Ninguna de las anteriores | Plan ligero (1-2 líneas, sin bloqueo) |

Adicionalmente verifica:
- ¿Lo que se implementa es consistente con la arquitectura existente?
- ¿Sigue los patrones del código existente?
- ¿Agrega solo lo pedido sin extras?

Si va a divergir de la arquitectura → se detiene y pregunta.

**Cache de sesión:** Si ya se aprobó un plan para ese módulo en la sesión actual, no re-pregunta hasta que cambie el contexto.

---

### `responsible-use.json` — Validación de prompt

| Campo | Valor |
|-------|-------|
| **Trigger** | UserPromptSubmit |
| **Tipo** | agent |

**Lógica:**

- No evalúa longitud del prompt
- Verifica si contiene: (a) acción reconocible + (b) objeto/entidad concreto
- Si ambos presentes → procede sin preguntar
- Si falta alguno → pregunta específicamente qué falta

---

### `code-review-gate.json` — Review post-escritura

| Campo | Valor |
|-------|-------|
| **Trigger** | PostToolUse |
| **Matcher** | `fs_write\|str_replace\|fs_append` |
| **Tipo** | agent |

**Qué hace:** Después de escribir código, recordar al usuario que revise: naming, error handling, tests necesarios, consistencia con arquitectura.

---

### `test-coverage-gate.json` — Verificación de tests

| Campo | Valor |
|-------|-------|
| **Trigger** | PostTaskExec |
| **Tipo** | agent |

**Qué hace:** Verifica que se crearon/actualizaron tests correspondientes. Si no hay tests para el código nuevo, informa y pide confirmación para continuar sin ellos.

---

### `build-validate.json` — Compilación post-save

| Campo | Valor |
|-------|-------|
| **Trigger** | PostFileSave |
| **Matcher** | `\.(java\|py\|js\|ts)$` |
| **Tipo** | command |

**Comando por stack:**

- Java: `./gradlew compileJava`
- Python: `ruff check`
- Node: `npm run lint`

---

### `integrity-check.json` — Verificación de integridad al inicio

| Campo | Valor |
|-------|-------|
| **Trigger** | SessionStart |
| **Tipo** | agent |

**Qué hace:** Al arrancar sesión, verifica si los hooks críticos (`pre-write-gate.json`) existen y están activos. Si falta alguno:

> ⚠️ `pre-write-gate` no está activo. Los cambios no pasarán por confirmación automática — operando en modo degradado.

No bloquea la sesión — informa. Si no hay hooks, el steering aplica autoevaluación como fallback (criterio de la tabla trivial/significativo), perdiendo determinismo pero manteniendo cobertura mínima.

---

### `summary-on-completion.json` — Resumen al finalizar

| Campo | Valor |
|-------|-------|
| **Trigger** | Stop |
| **Tipo** | agent |

**Qué hace:** Al finalizar sesión, presentar resumen de cambios realizados y pedir validación final del usuario. Sugerir ejecutar el Trash Inspector si hubo cambios significativos.

---

## 6. Fuera de alcance de este MCP

| Fuera | Responsable |
|-------|-------------|
| Frontend | MCP futuro dedicado |
| Base de datos (schemas, migraciones) | MCP futuro dedicado |
| Postman Collections | MCP futuro dedicado |
| Datadog dashboards/alertas | Equipo SRE |
| Seguridad diferenciada (solo backend vs con frontend) | Pendiente definición |
| CI/CD pipeline | Templates institucionales |
| Infraestructura cloud / Terraform | Repo `-infra` separado |
| Coordinación entre MCPs | Se define cuando existan al menos 2 MCPs desarrollados |
| Dockerfile / contenerización | Repo dedicado (sin valores quemados), indexado por `dockerProfile` |
| Valores reales de config por ambiente (Dev/Stage/Prod) | Repo `-infra` vía Terraform |
| Testing de integración / contract testing | Limitado a unit + mocks; ampliar depende de infraestructura no disponible hoy |

---

## 7. Valor Diferencial

| Sin MCP | Con MCP |
|---------|---------|
| Proyecto desde cero sin guía | Workspace con estándares embebidos desde el día 1 |
| Kiro genera sin restricciones | Kiro respeta convenciones y arquitectura del workspace |
| El agente diverge y toma atajos | Se ciñe a lo suministrado, confirma antes de desviarse |
| Usuario irresponsable sin saberlo | Sistema informa antes de que cometa errores |
| Tests opcionales en la práctica | Tests son parte del flujo obligatorio |
| Queries inseguras pasan | ORM obligatorio, SQL injection imposible |
| Observabilidad se agrega después | Configurada por ambiente desde el día 1 |
| Cada equipo inventa su estructura | Estructura consistente que escala sin trauma |
| El agente inventa funcionalidades | Solo implementa lo pedido, pregunta antes de agregar |
| Plan de trabajo invisible | Plan siempre visible, con profundidad proporcional al riesgo |

---

## 8. Decisiones diferidas (explícitamente fuera de alcance hoy)

| Decisión | Cuándo se resuelve |
|----------|-------------------|
| Coordinación entre MCPs (backend, frontend, DB) | Cuando existan al menos 2 MCPs |
| Observabilidad para Python/Node | Cuando se creen esas plantillas |
| Estrategia de seguridad backend-only vs con frontend | Cuando haya referente de ambos casos |
| Criterio definitivo de backward compatibility (90 días) | Con más contexto de uso real |
| Activación de steerings para proyectos externos al MCP | Detección única al primer arranque |
| Mensajería asíncrona (DLQ, retries, poison messages) | Sin caso de uso real aún |
| Rate limiting / circuit breaker (librería, umbral por stack) | Requiere definición con arquitectura |
| Modelo de autorización / acreditación de APIs | A la espera de definición del formato de acreditación existente |
| Política de actualización de dependencias (Dependabot/Renovate, SLA ante CVE) | No definida aún |

> **Regla para estos pendientes:** el MCP no debe generar implementación por defecto ni asumir un criterio propio en estos temas. Debe declarar explícitamente que están fuera de alcance hasta su definición, para evitar mandatos no autorizados o implementaciones a medias.

---

*Documento generado: 2026-07-16*
*Última actualización: 2026-07-16 (revisión de puntos de fuga: contenerización, config por ambiente, cache, i18n, connection pooling, commons, y pendientes explícitos)*
*Versión: 1.1.0*