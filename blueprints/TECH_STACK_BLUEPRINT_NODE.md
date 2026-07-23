# Blueprint Tecnico — Microservicio Node.js/Express (Seguros Bolivar)

> Documento de referencia para generacion automatizada de proyectos tipo microservicio con Node.js.
> Homologo del blueprint Java/Spring Boot, adaptado al ecosistema Node con los mismos principios
> de calidad, claridad y escalabilidad.

---

## Stack Tecnologico

| Componente | Version | Justificacion |
|------------|---------|---------------|
| Node.js | 22.x LTS | Soporte LTS activo hasta 2027-04, APIs modernas (fetch nativo, test runner) |
| TypeScript | 5.5+ | Type safety obligatorio — nunca JavaScript plano |
| npm | 10.x+ | Lockfile v3, workspaces nativos |
| Express | 4.21+ | Ecosistema maduro, middleware extensible, adopcion institucional |
| PostgreSQL | 15+ | Consistente con el stack Java |
| H2 / SQLite | (test) | Base liviana para tests unitarios |

> **Nota sobre Fastify:** Fastify 5.x es alternativa aprobada si el equipo lo justifica (mayor throughput,
> schema-based validation nativa). La estructura de proyecto y convenciones aplican igual.

---

## Dependencias Clave

### Core

| Paquete | Version | Proposito |
|---------|---------|-----------|
| express | ^4.21.0 | Framework HTTP |
| typescript | ^5.5.0 | Compilador TS |
| tsx | ^4.19.0 | Ejecucion directa TS en desarrollo |
| zod | ^3.23.0 | Validacion y parsing de schemas (runtime + tipos) |
| pg | ^8.13.0 | Cliente PostgreSQL con queries parametrizados |
| drizzle-orm | ^0.36.0 | ORM type-safe con query builder |
| drizzle-kit | ^0.28.0 | CLI para schema introspection |
| pino | ^9.5.0 | Logs estructurados JSON, alto rendimiento |
| pino-pretty | ^13.0.0 | Logs legibles en desarrollo (solo devDependency) |

### Seguridad

| Paquete | Version | Proposito |
|---------|---------|-----------|
| helmet | ^8.0.0 | Headers de seguridad (HSTS, CSP, X-Frame, etc.) |
| cors | ^2.8.5 | Configuracion CORS |
| passport | ^0.7.0 | Autenticacion pluggable |
| passport-jwt | ^4.0.1 | Estrategia JWT / OAuth2 resource server |
| jsonwebtoken | ^9.0.2 | Verificacion/decodificacion JWT |
| express-rate-limit | ^7.4.0 | Rate limiting por IP/ruta |
| hpp | ^0.2.3 | Proteccion HTTP Parameter Pollution |

### Observabilidad

| Paquete | Version | Proposito |
|---------|---------|-----------|
| @opentelemetry/sdk-node | ^0.56.0 | Tracing distribuido |
| @opentelemetry/auto-instrumentations-node | ^0.52.0 | Auto-instrumentacion Express/pg/http |
| dd-trace | ^5.27.0 | APM Datadog (alternativa a OTEL si ya existe infra) |
| prom-client | ^15.1.0 | Metricas Prometheus |

### AWS

| Paquete | Version | Proposito |
|---------|---------|-----------|
| @aws-sdk/client-ssm | ^3.700.0 | Parameter Store |
| @aws-sdk/client-secrets-manager | ^3.700.0 | Secrets Manager |
| @aws-sdk/client-s3 | ^3.700.0 | S3 (opcional) |
| @aws-sdk/client-sqs | ^3.700.0 | SQS (opcional) |

### Testing

| Paquete | Version | Proposito |
|---------|---------|-----------|
| vitest | ^2.1.0 | Test runner (mas rapido que Jest, soporte TS nativo) |
| supertest | ^7.0.0 | Tests HTTP integration |
| @faker-js/faker | ^9.2.0 | Datos de prueba |
| nock | ^14.0.0 | Mock de llamadas HTTP externas |
| testcontainers | ^10.14.0 | Contenedores efimeros para integration tests |

### Documentacion API

| Paquete | Version | Proposito |
|---------|---------|-----------|
| swagger-jsdoc | ^6.2.8 | Generacion OpenAPI desde JSDoc/decorators |
| swagger-ui-express | ^5.0.1 | UI Swagger embebida |

### Desarrollo

| Paquete | Version | Proposito |
|---------|---------|-----------|
| eslint | ^9.14.0 | Linter (flat config) |
| @typescript-eslint/eslint-plugin | ^8.13.0 | Reglas TS |
| prettier | ^3.4.0 | Formateo |
| husky | ^9.1.0 | Git hooks (pre-commit) |
| lint-staged | ^15.2.0 | Lint solo archivos staged |

### Supply Chain Security

| Paquete | Version | Proposito |
|---------|---------|-----------|
| lockfile-lint | ^4.14.0 | Valida que lockfile no apunte a registries externos |
| socket | ^2.0.0 | Analisis de comportamiento de dependencias (opcional CI) |

---

## Arquitectura de Directorios (Domain-Driven)

```
proyecto-ms/
├── src/
│   ├── app.ts                    ← Configuracion Express (middleware, routes, error handler)
│   ├── server.ts                 ← Entry point (listen, graceful shutdown)
│   ├── config/
│   │   ├── index.ts              ← Carga y valida env vars con Zod
│   │   ├── database.ts           ← Pool pg / Drizzle client
│   │   ├── logger.ts             ← Instancia Pino configurada
│   │   └── security.ts           ← Passport strategies, Helmet config
│   ├── commons/
│   │   ├── api-response.dto.ts   ← { codigo, mensaje, data }
│   │   ├── pagination.dto.ts     ← { page, size, totalPages, totalElements }
│   │   └── audit.mixin.ts        ← Campos auditoria (creadoPor, fechaCreacion, etc.)
│   ├── middleware/
│   │   ├── error-handler.ts      ← Global error handler (nunca stack trace al cliente)
│   │   ├── correlation-id.ts     ← X-Correlation-ID (lee o genera UUID)
│   │   ├── request-logger.ts     ← Log de request/response con Pino
│   │   ├── validate.ts           ← Middleware generico Zod (body, query, params)
│   │   └── auth.ts               ← Middleware Passport JWT
│   ├── errors/
│   │   ├── bolivar-business.error.ts  ← Error custom con codigo + httpStatus + categoria
│   │   └── error-types.enum.ts        ← NEGOCIO, VALIDACION, TECNICO, SEGURIDAD
│   ├── utils/
│   │   ├── data-sanitizer.ts     ← Sanitizacion XSS (escape HTML entities)
│   │   └── date.utils.ts         ← Helpers fecha ISO-8601
│   └── <dominio>/                ← Un dominio por carpeta
│       ├── <dominio>.controller.ts
│       ├── <dominio>.service.ts
│       ├── <dominio>.repository.ts
│       ├── <dominio>.schema.ts        ← Schemas Drizzle (tabla + relaciones)
│       └── dto/
│           ├── crear-<dominio>.dto.ts
│           ├── actualizar-<dominio>.dto.ts
│           ├── filtros-<dominio>.dto.ts
│           └── <dominio>-response.dto.ts
├── tests/
│   ├── unit/
│   │   └── <dominio>/
│   ├── integration/
│   │   └── <dominio>/
│   └── helpers/
│       ├── test-app.ts           ← Express app sin listen (para supertest)
│       └── factories/            ← Builders de datos de prueba
├── drizzle/
│   └── schema.ts                 ← Re-export de todos los schemas (para drizzle-kit)
├── infra/
│   ├── docker-compose.yml
│   ├── seed-localstack-ssm.sh
│   ├── mock-oauth-config.json
│   └── .env.sample
├── .github/
│   ├── workflows/
│   │   └── pipeline.yaml
│   └── pull_request_template.md
├── tsconfig.json
├── vitest.config.ts
├── eslint.config.mjs
├── .prettierrc
├── package.json
├── .npmrc                        ← Registry Artifactory + ignore-scripts + audit
├── .env                          ← Git-ignored, copiado de .env.sample
├── .gitignore
└── README.md
```

Agregar un nuevo dominio:

```
└── src/
    └── <nuevo-dominio>/     ← Se agrega sin tocar los existentes
        ├── <nuevo-dominio>.controller.ts
        ├── <nuevo-dominio>.service.ts
        ├── <nuevo-dominio>.repository.ts
        ├── <nuevo-dominio>.schema.ts
        └── dto/
```

---

## Patrones de Implementacion

### Respuesta API estandar

```typescript
interface ApiResponse<T> {
  codigo: string;
  mensaje: string;
  data: T | null;
}

// Uso en controller
res.status(200).json({
  codigo: "OK",
  mensaje: "Operacion exitosa",
  data: resultado,
});
```

### Error de negocio

```typescript
throw new BolivarBusinessError({
  codigo: "ENTIDAD_NO_ENCONTRADA",
  mensaje: "No se encontro el recurso solicitado",
  categoria: ErrorType.NEGOCIO,
  httpStatus: 404,
});
```

### Controller

```typescript
@Route("/api/v1/terceros")
export class TerceroController {
  constructor(private readonly service: TerceroService) {}

  async crear(req: Request, res: Response, next: NextFunction) {
    const dto = crearTerceroSchema.parse(req.body);
    const resultado = await this.service.crear(dto);
    res.status(201).json({ codigo: "OK", mensaje: "Creado", data: resultado });
  }
}
```

### Service

```typescript
export class TerceroService {
  constructor(private readonly repository: TerceroRepository) {}

  async crear(dto: CrearTerceroDto): Promise<TerceroResponseDto> {
    // Logica de negocio
    const entity = await this.repository.insertar(dto);
    return TerceroResponseDto.fromEntity(entity);
  }
}
```

### Repository (Drizzle)

```typescript
export class TerceroRepository {
  constructor(private readonly db: DrizzleClient) {}

  async buscarPorId(id: number): Promise<Tercero | null> {
    const [result] = await this.db
      .select()
      .from(terceros)
      .where(eq(terceros.id, id))
      .limit(1);
    return result ?? null;
  }

  async listarConFiltros(filtros: FiltrosTerceroDto) {
    const query = this.db.select().from(terceros);
    // Filtros dinamicos con condiciones encadenadas
    if (filtros.nombre) query.where(ilike(terceros.nombre, `%${filtros.nombre}%`));
    return query.limit(filtros.size).offset(filtros.page * filtros.size);
  }
}
```

### Validacion con Zod

```typescript
export const crearTerceroSchema = z.object({
  nombre: z.string().min(1).max(200).trim(),
  documento: z.string().regex(/^\d{5,15}$/),
  tipoDocumento: z.enum(["CC", "NIT", "CE", "PP"]),
  email: z.string().email().optional(),
});

export type CrearTerceroDto = z.infer<typeof crearTerceroSchema>;
```

### Middleware de validacion

```typescript
export function validate(schema: ZodSchema) {
  return (req: Request, _res: Response, next: NextFunction) => {
    schema.parse(req.body);
    next();
  };
}

// Uso en router
router.post("/", validate(crearTerceroSchema), controller.crear);
```

---

## Configuracion (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "declaration": true,
    "sourceMap": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

Reglas criticas:
- `strict: true` — no negociable
- `noUncheckedIndexedAccess: true` — previene undefined silenciosos
- Nunca `any` — usar `unknown` y narrowing
- Nunca `as` casting salvo en tests o boundaries bien definidos

---

## Infraestructura Local

- Docker Compose: LocalStack (SSM, S3, SQS) + Mock OAuth + Datadog Agent (no-forward)
- Perfiles via NODE_ENV: `local` (PostgreSQL via SSM), `test` (SQLite o testcontainers)
- CI/CD: GitHub Actions con templates institucionales
- Hot reload: tsx watch en desarrollo

---

## Seguridad

### Headers (via Helmet)

HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy, CSP.

### Autenticacion

Estrategia pluggable via Passport.js:
- `oauth2-resource-server`: JWT validation contra JWKS del IdP
- `api-gateway-delegated`: headers pre-validados por API Gateway
- `machine-to-machine`: client_credentials grant
- `deferred`: sin auth configurada (solo para prototipos con confirmacion)

### Input validation

- Zod en TODA entrada (body, query, params, headers custom)
- Nunca `req.body` sin parsear
- Sanitizacion XSS en responses (HTML entity encoding)
- `hpp` para prevenir HTTP Parameter Pollution

### Secrets

Nunca en codigo. Via AWS SSM Parameter Store o variables de entorno. Jamas en .env commiteado.

---

## Observabilidad

### Logs (Pino)

| Ambiente | Nivel | Formato | Masking |
|----------|-------|---------|---------|
| Local | debug | Consola legible (pino-pretty) | OFF |
| Productivo | info | JSON estructurado | ON |

### Correlation ID

Middleware que lee `X-Correlation-ID` del request o genera UUID v4. Se inyecta en AsyncLocalStorage para propagacion automatica a logs y downstream calls.

### Health check

```
GET /health → { status: "UP", timestamp: "ISO-8601" }
GET /health/ready → verifica conexion DB + dependencias criticas
```

### Metricas

Endpoint `/metrics` con prom-client: request duration, request count by status, active connections, event loop lag.

---

## Testing

| Tipo | Herramienta | Ubicacion |
|------|-------------|-----------|
| Unit | Vitest | tests/unit/ |
| Integration | Vitest + Supertest | tests/integration/ |
| Coverage | vitest --coverage (v8) | Min 80% |
| Mocks HTTP | nock | Servicios externos |
| Containers | testcontainers | PostgreSQL efimero |

### Patron

```typescript
describe("TerceroService", () => {
  it("debe crear un tercero con datos validos", async () => {
    // Arrange
    const dto = TerceroFactory.buildCrearDto();
    // Act
    const resultado = await service.crear(dto);
    // Assert
    expect(resultado.id).toBeDefined();
    expect(resultado.nombre).toBe(dto.nombre);
  });
});
```

### Scripts package.json

```json
{
  "scripts": {
    "dev": "tsx watch --env-file=.env src/server.ts",
    "build": "tsc",
    "start": "node --env-file=.env dist/server.js",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/"
  }
}
```

---

## Naming Conventions

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Archivos | kebab-case | `tercero.controller.ts` |
| Clases | PascalCase | `TerceroController` |
| Funciones/metodos | camelCase | `buscarPorId` |
| Variables | camelCase | `terceroActivo` |
| Constantes | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |
| Interfaces | PascalCase (sin prefijo I) | `TerceroResponse` |
| Types | PascalCase | `CrearTerceroDto` |
| Enums | PascalCase + UPPER_SNAKE valores | `ErrorType.NEGOCIO` |
| Schemas Zod | camelCase + Schema suffix | `crearTerceroSchema` |
| Tablas DB (Drizzle) | snake_case plural | `terceros` |
| Columnas DB | snake_case | `fecha_creacion` |

---

## Graceful Shutdown

```typescript
const server = app.listen(port);

process.on("SIGTERM", async () => {
  logger.info("SIGTERM recibido, cerrando conexiones...");
  server.close();
  await pool.end();
  process.exit(0);
});
```

---

## Dependencias — Gobernanza y Seguridad de Supply Chain

### Principio: superficie minima

Cada dependencia es un vector de ataque. Antes de instalar un paquete, verificar:

1. Existe equivalente nativo en Node 22?
2. Cuantas dependencias transitivas trae? (`npm explain <pkg>`)
3. Quien lo mantiene, con que frecuencia, y cuantos maintainers tiene?
4. Tiene alternativa con zero-deps?
5. Un microservicio no deberia superar ~30 dependencias directas de produccion

### Nativos que reemplazan paquetes

| Antes (paquete) | Ahora (nativo Node 22) | Desde |
|---|---|---|
| `node-fetch` | `fetch` global | Node 18 |
| `uuid` | `crypto.randomUUID()` | Node 19 |
| `dotenv` | `node --env-file=.env` | Node 20 |
| `chalk` | `util.styleText()` | Node 21 |
| `lodash.groupBy` | `Object.groupBy()` | Node 21 |
| `lodash.cloneDeep` | `structuredClone()` | Node 17 |
| `abort-controller` | `AbortController` global | Node 16 |
| `util.promisify(setTimeout)` | `import { setTimeout } from 'timers/promises'` | Node 16 |

### `.npmrc` — template obligatorio (commiteado al repo)

```ini
# Registry institucional — toda dependencia pasa por Artifactory
registry=https://artifactory.segurosbolivar.com/api/npm/npm-remote/

# Scopes internos apuntan al registry privado (previene dependency confusion)
@bolivar:registry=https://artifactory.segurosbolivar.com/api/npm/npm-private/

# Bloquear scripts de lifecycle (postinstall, preinstall)
# Vector de ataque #1 en npm — desactivado por defecto
ignore-scripts=true

# Lockfile obligatorio — npm ci falla si no existe
package-lock=true

# Audit automatico en cada install
audit=true

# Sin sponsorship noise
fund=false

# Nivel de audit que bloquea install
audit-level=high
```

Si un paquete legitimo requiere scripts (ej. `esbuild`, `sharp`, `bcrypt`), se habilita
selectivamente en `package.json`:

```json
{
  "trustedDependencies": ["esbuild", "sharp"]
}
```

### Lockfile — primera linea de defensa

```bash
# CI SIEMPRE usa npm ci, nunca npm install
npm ci

# Validar integridad del lockfile (detecta registry injection)
npx lockfile-lint \
  --path package-lock.json \
  --type npm \
  --allowed-hosts artifactory.segurosbolivar.com
```

`npm ci`:
- Instala exactamente lo que dice `package-lock.json`
- Valida SHA-512 de cada paquete (campo `integrity`)
- Falla si `package.json` y `package-lock.json` divergen
- Un patch malicioso publicado despues del lock no entra hasta que un humano haga `npm install`

### Dependency confusion — prevencion

Si Seguros Bolivar tiene paquetes internos con scope `@bolivar`, un atacante puede publicar
el mismo nombre en npmjs.com con version mas alta. npm resuelve la version mayor por defecto.

Mitigacion (ya incluida en `.npmrc`):
- Scope `@bolivar` apunta exclusivamente al registry privado
- `lockfile-lint` valida que ninguna URL apunte a registries no autorizados
- En Artifactory: activar "Exclude Patterns" para bloquear paquetes con scope `@bolivar` del proxy remoto

### Pipeline CI — audit obligatorio

```yaml
# En pipeline.yaml
- name: Install dependencies
  run: npm ci

- name: Lockfile integrity
  run: |
    npx lockfile-lint \
      --path package-lock.json \
      --type npm \
      --allowed-hosts artifactory.segurosbolivar.com

- name: Security audit
  run: npm audit --audit-level=high

- name: Deep dependency scan
  run: npx socket scan . --strict
  continue-on-error: true  # advisory hasta madurar la herramienta

- name: Generate SBOM
  run: npx @cyclonedx/cyclonedx-npm --output-file sbom.json
```

### Reglas de gobernanza

| Regla | Detalle |
|-------|---------|
| Registry | Solo JFrog Artifactory (configurado en `.npmrc` commiteado) |
| Versiones | Pinned en `package-lock.json` (nunca `*`, `latest`, o rangos amplios como `>=`) |
| Scripts | `ignore-scripts=true` por defecto, allowlist explicita en `trustedDependencies` |
| Audit | `npm audit --audit-level=high` bloquea el pipeline si hay vulnerabilidades high/critical |
| Lockfile | `lockfile-lint` valida registries permitidos |
| SBOM | Generado con CycloneDX en cada release |
| Limite | Max ~30 dependencias directas de produccion por microservicio |
| Nuevas deps | Requieren justificacion: por que no nativo, cuantas transitivas, quien mantiene |

### Incidentes de referencia (por que estas reglas existen)

| Incidente | Ano | Vector | Que habria mitigado |
|---|---|---|---|
| `event-stream` | 2018 | postinstall malicioso | `ignore-scripts=true` |
| `ua-parser-js` | 2021 | maintainer comprometido, postinstall crypto-miner | `ignore-scripts=true` + audit |
| `node-ipc` | 2022 | maintainer inyecto codigo destructivo en patch | `npm ci` (lockfile fijo) |
| `colors`/`faker` | 2022 | maintainer saboteo sus propios paquetes | `npm ci` + lockfile fijo |
| `@azure/identity` | 2023 | dependency confusion | `.npmrc` con scope privado |

---

*Generado por MCP_INIT_MS_SegurosBolivar v1.0.0*
