# Blueprint Tecnico — Microservicio Python/FastAPI (Seguros Bolivar)

> Documento de referencia para generacion automatizada de proyectos tipo microservicio con Python.
> Homologo del blueprint Java/Spring Boot, adaptado al ecosistema Python con los mismos principios
> de calidad, claridad y escalabilidad.

---

## Stack Tecnologico

| Componente | Version | Justificacion |
|------------|---------|---------------|
| Python | 3.12+ | Pattern matching, ExceptionGroups, performance improvements, LTS activo |
| Poetry | 1.8+ | Lockfile determinista, dependency groups, build system PEP 517 |
| FastAPI | 0.115+ | Async nativo, validacion automatica, OpenAPI generado, alto rendimiento |
| Uvicorn | 0.32+ | ASGI server, HTTP/1.1 y HTTP/2 |
| PostgreSQL | 15+ | Consistente con el stack Java |
| SQLite | (test) | Base liviana para tests unitarios |

> **Nota sobre uv:** uv (Astral) es alternativa aprobada como gestor de dependencias si el equipo
> lo justifica (velocidad 10-100x sobre pip/poetry). La estructura de proyecto aplica igual,
> cambiando `pyproject.toml` por la seccion `[tool.uv]`.

---

## Dependencias Clave

### Core

| Paquete | Version | Proposito |
|---------|---------|-----------|
| fastapi | ^0.115.0 | Framework ASGI |
| uvicorn[standard] | ^0.32.0 | Server ASGI con uvloop |
| pydantic | ^2.10.0 | Validacion, serialization, settings |
| pydantic-settings | ^2.6.0 | Carga de config desde env vars / .env |
| sqlalchemy[asyncio] | ^2.0.36 | ORM async con type hints |
| asyncpg | ^0.30.0 | Driver PostgreSQL async |
| greenlet | ^3.1.0 | Requerido por SQLAlchemy async |
| python-dotenv | ^1.0.1 | Carga .env en desarrollo |
| structlog | ^24.4.0 | Logs estructurados con procesadores |

### Seguridad

| Paquete | Version | Proposito |
|---------|---------|-----------|
| python-jose[cryptography] | ^3.3.0 | Decodificacion/verificacion JWT |
| passlib[bcrypt] | ^1.7.4 | Hashing de passwords (si aplica) |
| starlette-csrf | ^3.0.0 | Proteccion CSRF |
| secure | ^1.0.0 | Headers de seguridad (HSTS, CSP, X-Frame, etc.) |

### Observabilidad

| Paquete | Version | Proposito |
|---------|---------|-----------|
| opentelemetry-sdk | ^1.28.0 | Tracing distribuido |
| opentelemetry-instrumentation-fastapi | ^0.49b0 | Auto-instrumentacion FastAPI |
| opentelemetry-instrumentation-sqlalchemy | ^0.49b0 | Auto-instrumentacion SQLAlchemy |
| opentelemetry-exporter-otlp | ^1.28.0 | Exportador OTLP (Datadog/Jaeger) |
| ddtrace | ^2.16.0 | APM Datadog (alternativa a OTEL si ya existe infra) |
| prometheus-fastapi-instrumentator | ^7.0.0 | Metricas Prometheus |

### AWS

| Paquete | Version | Proposito |
|---------|---------|-----------|
| boto3 | ^1.35.0 | SDK AWS (SSM, Secrets Manager, S3, SQS) |
| aiobotocore | ^2.15.0 | Cliente async para AWS |
| types-boto3 | ^1.35.0 | Type stubs para boto3 |

### Testing

| Paquete | Version | Proposito |
|---------|---------|-----------|
| pytest | ^8.3.0 | Test runner |
| pytest-asyncio | ^0.24.0 | Soporte async en tests |
| pytest-cov | ^6.0.0 | Coverage (min 80%) |
| httpx | ^0.28.0 | Cliente HTTP async + test client FastAPI |
| factory-boy | ^3.3.1 | Factories de datos de prueba |
| respx | ^0.22.0 | Mock de llamadas httpx |
| testcontainers[postgres] | ^4.8.0 | Contenedores efimeros |

### Desarrollo

| Paquete | Version | Proposito |
|---------|---------|-----------|
| ruff | ^0.8.0 | Linter + formatter (reemplaza flake8 + isort + black) |
| mypy | ^1.13.0 | Type checker estatico |
| pre-commit | ^4.0.0 | Git hooks |
| sqlalchemy[mypy] | ^2.0.36 | Plugin mypy para SQLAlchemy |

---

## Arquitectura de Directorios (Domain-Driven)

```
proyecto-ms/
├── src/
│   ├── __init__.py
│   ├── main.py                        ← Entry point FastAPI (app factory)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                ← Pydantic Settings (env vars validadas)
│   │   ├── database.py                ← AsyncEngine + AsyncSession factory
│   │   ├── logging.py                 ← Configuracion structlog
│   │   └── security.py               ← Dependencias auth (JWT decode, strategies)
│   ├── commons/
│   │   ├── __init__.py
│   │   ├── api_response.py            ← ApiResponse[T] (codigo, mensaje, data)
│   │   ├── pagination.py              ← PaginatedResponse, PaginationParams
│   │   └── audit_mixin.py             ← Mixin SQLAlchemy (creado_por, fecha_creacion, etc.)
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── correlation_id.py          ← X-Correlation-ID (lee o genera UUID)
│   │   ├── error_handler.py           ← Exception handlers globales
│   │   ├── request_logger.py          ← Log request/response con structlog
│   │   └── security_headers.py        ← HSTS, CSP, X-Frame, etc.
│   ├── errors/
│   │   ├── __init__.py
│   │   ├── bolivar_business_error.py  ← Error custom con codigo + http_status + categoria
│   │   └── error_types.py             ← Enum: NEGOCIO, VALIDACION, TECNICO, SEGURIDAD
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_sanitizer.py          ← Sanitizacion XSS
│   │   └── date_utils.py              ← Helpers fecha ISO-8601
│   └── <dominio>/                     ← Un dominio por carpeta
│       ├── __init__.py
│       ├── router.py                  ← APIRouter con endpoints
│       ├── service.py                 ← Logica de negocio
│       ├── repository.py              ← Acceso a datos (SQLAlchemy)
│       ├── models.py                  ← Modelos SQLAlchemy (tabla + relaciones)
│       └── schemas/
│           ├── __init__.py
│           ├── crear_<dominio>.py
│           ├── actualizar_<dominio>.py
│           ├── filtros_<dominio>.py
│           └── <dominio>_response.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    ← Fixtures globales (app, client, db session)
│   ├── unit/
│   │   └── <dominio>/
│   ├── integration/
│   │   └── <dominio>/
│   └── factories/
│       └── <dominio>_factory.py       ← Factory Boy
├── infra/
│   ├── docker-compose.yml
│   ├── seed-localstack-ssm.sh
│   ├── mock-oauth-config.json
│   └── .env.sample
├── .github/
│   ├── workflows/
│   │   └── pipeline.yaml
│   └── pull_request_template.md
├── pyproject.toml                     ← Poetry config + ruff + mypy + pytest
├── poetry.lock
├── Dockerfile
├── .env                               ← Git-ignored
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

Agregar un nuevo dominio:

```
└── src/
    └── <nuevo_dominio>/     ← Se agrega sin tocar los existentes
        ├── __init__.py
        ├── router.py
        ├── service.py
        ├── repository.py
        ├── models.py
        └── schemas/
```

---

## Patrones de Implementacion

### Respuesta API estandar

```python
from pydantic import BaseModel, Generic, TypeVar

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    codigo: str
    mensaje: str
    data: T | None = None
```

### Error de negocio

```python
raise BolivarBusinessError(
    codigo="ENTIDAD_NO_ENCONTRADA",
    mensaje="No se encontro el recurso solicitado",
    categoria=ErrorType.NEGOCIO,
    http_status=404,
)
```

### Router (Controller equivalente)

```python
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/api/v1/terceros", tags=["Terceros"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_tercero(
    dto: CrearTerceroSchema,
    service: TerceroService = Depends(get_tercero_service),
) -> ApiResponse[TerceroResponseSchema]:
    resultado = await service.crear(dto)
    return ApiResponse(codigo="OK", mensaje="Creado", data=resultado)
```

### Service

```python
class TerceroService:
    def __init__(self, repository: TerceroRepository) -> None:
        self._repository = repository

    async def crear(self, dto: CrearTerceroSchema) -> TerceroResponseSchema:
        entity = await self._repository.insertar(dto)
        return TerceroResponseSchema.model_validate(entity)
```

### Repository (SQLAlchemy 2.x async)

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class TerceroRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def buscar_por_id(self, id: int) -> Tercero | None:
        stmt = select(Tercero).where(Tercero.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_con_filtros(
        self, filtros: FiltrosTerceroSchema, page: int, size: int
    ) -> list[Tercero]:
        stmt = select(Tercero)
        if filtros.nombre:
            stmt = stmt.where(Tercero.nombre.ilike(f"%{filtros.nombre}%"))
        stmt = stmt.offset(page * size).limit(size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
```

### Modelo SQLAlchemy

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer

class Base(DeclarativeBase):
    pass

class Tercero(AuditMixin, Base):
    __tablename__ = "terceros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    documento: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    tipo_documento: Mapped[str] = mapped_column(String(3), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
```

### Schema Pydantic (DTO equivalente)

```python
from pydantic import BaseModel, EmailStr, Field
from enum import StrEnum

class TipoDocumento(StrEnum):
    CC = "CC"
    NIT = "NIT"
    CE = "CE"
    PP = "PP"

class CrearTerceroSchema(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    documento: str = Field(pattern=r"^\d{5,15}$")
    tipo_documento: TipoDocumento
    email: EmailStr | None = None
```

### Dependency Injection (FastAPI Depends)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

def get_tercero_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TerceroRepository:
    return TerceroRepository(session)

def get_tercero_service(
    repo: TerceroRepository = Depends(get_tercero_repository),
) -> TerceroService:
    return TerceroService(repo)
```

---

## Configuracion (pyproject.toml)

```toml
[tool.poetry]
name = "proyecto-ms"
version = "0.1.0"
python = "^3.12"

[tool.ruff]
target-version = "py312"
line-length = 120
src = ["src"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "S",      # bandit (seguridad)
    "B",      # bugbear
    "A",      # builtins
    "C4",     # comprehensions
    "DTZ",    # datetime timezone
    "T20",    # print statements
    "RUF",    # ruff-specific
    "ASYNC",  # async rules
    "PTH",    # pathlib
]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
plugins = ["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--strict-markers -ra"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "src/config/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

Reglas criticas:
- `mypy --strict` — no negociable
- Nunca `Any` — usar `object` o Protocol y narrowing
- Nunca `# type: ignore` sin justificacion en comentario
- `ruff` con regla `S` (bandit) activa — detecta problemas de seguridad en lint
- `T20` activa — detecta `print()` olvidados

---

## Infraestructura Local

- Docker Compose: LocalStack (SSM, S3, SQS) + Mock OAuth + Datadog Agent (no-forward)
- Perfiles via `APP_ENV`: `local` (PostgreSQL via SSM), `test` (SQLite o testcontainers)
- CI/CD: GitHub Actions con templates institucionales
- Hot reload: `uvicorn --reload` en desarrollo

---

## Seguridad

### Headers (via middleware)

HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy, CSP.

### Autenticacion

Estrategia pluggable via FastAPI dependencies:
- `oauth2-resource-server`: JWT validation contra JWKS del IdP (python-jose)
- `api-gateway-delegated`: headers pre-validados por API Gateway
- `machine-to-machine`: client_credentials grant
- `deferred`: sin auth configurada (solo para prototipos con confirmacion)

### Input validation

- Pydantic v2 en TODA entrada (body, query, path params, headers custom)
- FastAPI valida automaticamente con los type hints del endpoint
- Sanitizacion XSS en responses (HTML entity encoding)
- Nunca `**kwargs` o `dict` sin tipo en endpoints

### Secrets

Nunca en codigo. Via AWS SSM Parameter Store o variables de entorno. Jamas en .env commiteado.

---

## Observabilidad

### Logs (structlog)

| Ambiente | Nivel | Formato | Masking |
|----------|-------|---------|---------|
| Local | DEBUG | Consola legible (ConsoleRenderer) | OFF |
| Productivo | INFO | JSON estructurado (JSONRenderer) | ON |

### Correlation ID

Middleware ASGI que lee `X-Correlation-ID` del request o genera UUID v4. Se inyecta en `contextvars.ContextVar` para propagacion automatica a logs y downstream calls.

### Health check

```
GET /health → { "status": "UP", "timestamp": "ISO-8601" }
GET /health/ready → verifica conexion DB + dependencias criticas
```

### Metricas

Endpoint `/metrics` con prometheus-fastapi-instrumentator: request duration, request count by status, active connections.

---

## Testing

| Tipo | Herramienta | Ubicacion |
|------|-------------|-----------|
| Unit | pytest | tests/unit/ |
| Integration | pytest + httpx AsyncClient | tests/integration/ |
| Coverage | pytest-cov | Min 80% |
| Mocks HTTP | respx | Servicios externos |
| Containers | testcontainers | PostgreSQL efimero |

### Patron

```python
class TestTerceroService:
    async def test_crear_tercero_con_datos_validos(
        self, service: TerceroService, tercero_factory: TerceroFactory
    ):
        # Arrange
        dto = tercero_factory.build_crear_schema()
        # Act
        resultado = await service.crear(dto)
        # Assert
        assert resultado.id is not None
        assert resultado.nombre == dto.nombre
```

### Fixture principal (conftest.py)

```python
@pytest.fixture
async def app() -> AsyncGenerator[FastAPI, None]:
    app = create_app()
    yield app

@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
```

### Scripts pyproject.toml

```toml
[tool.poetry.scripts]
dev = "uvicorn src.main:app --reload --port 8080"
start = "uvicorn src.main:app --port 8080"
```

Comandos:
```bash
poetry run pytest                    # tests
poetry run pytest --cov              # tests + coverage
poetry run ruff check src/           # lint
poetry run ruff format src/          # format
poetry run mypy src/                 # type check
```

---

## Naming Conventions

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Archivos/modulos | snake_case | `tercero_service.py` |
| Clases | PascalCase | `TerceroService` |
| Funciones/metodos | snake_case | `buscar_por_id` |
| Variables | snake_case | `tercero_activo` |
| Constantes | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |
| Schemas Pydantic | PascalCase + Schema suffix | `CrearTerceroSchema` |
| Modelos SQLAlchemy | PascalCase singular | `Tercero` |
| Tablas DB | snake_case plural | `terceros` |
| Columnas DB | snake_case | `fecha_creacion` |
| Enums | PascalCase + UPPER valores | `ErrorType.NEGOCIO` |
| Routers (APIRouter) | snake_case | `tercero_router` |
| Packages (dominios) | snake_case | `consultar_terceros` |

---

## Graceful Shutdown

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db_pool()
    logger.info("Aplicacion iniciada")
    yield
    # Shutdown
    await close_db_pool()
    logger.info("Conexiones cerradas")

app = FastAPI(lifespan=lifespan)
```

---

## Dependencias — Gobernanza

- Todas las dependencias de JFrog Artifactory (source configurado en `pyproject.toml` o `~/.config/pip/pip.conf`)
- Versiones pinned en `poetry.lock` (nunca `*` o `latest`)
- `pip audit` o `safety check` en pipeline CI
- SBOM generado en release
- `ruff` con regla `S` (bandit) en lint para deteccion de vulnerabilidades estaticas

---

*Generado por MCP_INIT_MS_SegurosBolivar v1.0.0*
