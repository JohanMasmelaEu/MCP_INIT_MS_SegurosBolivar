# MCP_INIT_MS_SegurosBolivar

MCP Server para la inicializacion automatizada de microservicios en Seguros Bolivar. Genera arquetipos completos de proyectos listos para desarrollo local con Docker Compose (LocalStack, Mock OAuth, Datadog Agent).

Stacks soportados:

| Stack | Runtime | Framework | ORM | Status |
|-------|---------|-----------|-----|--------|
| `java-spring-boot` | JDK 21 | Spring Boot 4.x + Gradle 9.x | Spring Data JPA | Disponible |
| `node-express` | Node.js 22 | Express 4.x + TypeScript 5.x | Drizzle ORM | Disponible |
| `python-fastapi` | Python 3.12 | FastAPI + uv | SQLAlchemy 2.x async | Disponible |

---

## Requisitos

- **Docker Desktop** instalado y corriendo (unico requisito de software)
- **Kiro IDE** (o cualquier cliente MCP compatible con transport stdio)

> **No se necesita Python, Java, ni ningun runtime instalado en la maquina.**
> Todo corre dentro del contenedor Docker.

---

## Inicio Rapido (3 pasos)

### 1. Crear el archivo de configuracion MCP

Crear (o editar) `~/.kiro/settings/mcp.json` (configuracion global) o `<tu-workspace>/.kiro/settings/mcp.json` (solo ese proyecto):

```json
{
  "mcpServers": {
    "MCP_INIT_MS_SegurosBolivar": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--pull", "always",
        "-v", "<TU_RUTA_LOCAL>:/repos",
        "-v", "mcp-init-settings:/settings",
        "ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest"
      ],
      "disabled": false
    }
  }
}
```

### Configuracion del volumen (bind mount)

El volumen `-v <TU_RUTA_LOCAL>:/repos` mapea una carpeta de tu maquina al path `/repos` dentro del contenedor. Los proyectos generados se escriben ahi.

**Reemplaza `<TU_RUTA_LOCAL>`** con la ruta absoluta de tu carpeta de repositorios. Ejemplos segun sistema operativo:

| Sistema | Ejemplo | Resultado en mcp.json |
|---------|---------|----------------------|
| Windows | `C:\REPOS\SegurosBolivar` | `"-v", "C:/REPOS/SegurosBolivar:/repos"` |
| Windows | `D:\Proyectos` | `"-v", "D:/Proyectos:/repos"` |
| macOS/Linux | `/home/usuario/repos` | `"-v", "/home/usuario/repos:/repos"` |

> **IMPORTANTE:** El path destino SIEMPRE debe ser `:/repos`. Nunca cambies esta parte.
> El contenedor espera encontrar y escribir proyectos en `/repos`.
> Si montas en otro path (como `:/` o `:/workspace`), el contenedor no funcionara.

Ejemplo completo para un desarrollador cuya carpeta de trabajo es `C:\MisProyectos\Bolivar`:

```json
"-v", "C:/MisProyectos/Bolivar:/repos",
```

Esto hace que cuando el MCP genere un proyecto en `/repos/mi-microservicio`, los archivos aparezcan en `C:\MisProyectos\Bolivar\mi-microservicio` en tu maquina.

### Resumen de volumenes

| Volumen en mcp.json | Path dentro del contenedor | Tipo | Proposito |
|---------------------|---------------------------|------|-----------|
| `<TU_RUTA_LOCAL>:/repos` | `/repos` | Bind mount | Tu carpeta de repos local. Aqui se generan los proyectos. |
| `mcp-init-settings:/settings` | `/settings` | Volumen nombrado | Persiste la configuracion del MCP (directorio de salida) entre sesiones. |

### Flags adicionales

| Flag | Proposito |
|------|-----------|
| `--pull always` | Garantiza que Docker descargue la ultima version de la imagen cada vez que Kiro inicie el MCP. Nunca ejecutaras una version desactualizada. |
| `--rm` | Destruye el contenedor al cerrar sesion. La configuracion persiste en el volumen `mcp-init-settings`. |
| `-i` | Modo interactivo (requerido para comunicacion stdio con Kiro). |

> **Esta es la unica configuracion que necesitas hacer.** Una vez configurado, nunca mas se modifica.

### 2. Reiniciar sesion de Kiro

Cierra y abre el chat en Kiro para que lea la nueva configuracion.
Docker Desktop descargara la imagen automaticamente la primera vez (~150MB).

### 3. Verificar

Escribe en Kiro:

> "Lista los stacks disponibles del MCP de inicializacion"

Deberia responder con los 3 stacks disponibles: `java-spring-boot`, `node-express`, `python-fastapi`. Si lo hace, el MCP esta funcionando.

---

## Configuracion del directorio de salida

El MCP permite configurar **una sola vez** donde se generan los proyectos. Despues de eso, no necesitas especificar rutas en cada generacion.

### Opcion A: Configuracion automatica (recomendada)

Dile a Kiro en el chat:

> "Configura el directorio de salida del MCP a /repos/SegurosBolivar"

Kiro invocara `set_output_directory` y a partir de ese momento todos los proyectos se generan en `C:\REPOS\SegurosBolivar\<nombre-proyecto>`.

### Opcion B: Override puntual

Si necesitas generar un proyecto en otro lugar, simplemente indicalo:

> "Genera el proyecto en /repos/OtroEquipo"

Kiro pasara `target_path="/repos/OtroEquipo"` y el proyecto se creara ahi sin modificar la configuracion persistida.

### Mapeo de rutas (contenedor ↔ host)

Ejemplo si montaste `C:/REPOS/SegurosBolivar:/repos`:

| Dentro del contenedor | En tu maquina |
|-----------------------|---------------|
| `/repos` | `C:\REPOS\SegurosBolivar` |
| `/repos/mi-ms` | `C:\REPOS\SegurosBolivar\mi-ms` |
| `/repos/otro-proyecto` | `C:\REPOS\SegurosBolivar\otro-proyecto` |

El MCP siempre trabaja con rutas `/repos/...` internamente. Tu solo ves los archivos aparecer en tu carpeta local.

---

## Como funciona

### Arquitectura de comunicacion

```
┌─────────────────────────────────────────────────────────────────┐
│  Kiro IDE (tu maquina)                                          │
│                                                                 │
│  1. Lee .kiro/settings/mcp.json                                 │
│  2. Ejecuta: docker run -i --rm --pull always                   │
│     -v <TU_RUTA>:/repos -v mcp-init-settings:/settings <imagen> │
│  3. Conecta al proceso via stdio (stdin/stdout)                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Contenedor Docker (mcp-init-ms-segurosbolivar)           │  │
│  │                                                           │  │
│  │  Python 3.12 + MCP SDK                                    │  │
│  │  ├── Recibe llamadas JSON-RPC via stdin                   │  │
│  │  ├── Ejecuta tools (get_project_plan, initialize, etc.)   │  │
│  │  ├── Escribe archivos en /repos (bind mount al host)      │  │
│  │  ├── Persiste config en /settings (volumen nombrado)      │  │
│  │  └── Responde resultados via stdout                       │  │
│  │                                                           │  │
│  │  /repos ← bind mount desde tu carpeta local               │  │
│  │  /settings ← volumen nombrado (persiste entre sesiones)   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  4. Kiro recibe respuestas y las presenta al usuario            │
│  5. Al cerrar sesion → contenedor se destruye (--rm)            │
│     pero /settings persiste en el volumen nombrado              │
└─────────────────────────────────────────────────────────────────┘
```

### Ciclo de vida

1. **Kiro inicia sesion** → lee `mcp.json` → arranca el contenedor Docker
2. **Handshake:** Kiro pregunta que tools tiene el MCP → MCP responde con 8 tools
3. **Conversacion:** Kiro invoca tools segun la peticion del usuario
4. **Generacion:** El MCP escribe archivos en `/repos` (tu carpeta de repos local)
5. **Cierre:** Kiro termina sesion → contenedor se destruye automaticamente
   - La configuracion (output directory) persiste en el volumen `mcp-init-settings`

El MCP **no se arranca manualmente**. Kiro lo gestiona completo.

### Flujo de interaccion tipico

```
Tu: "Inicializa un microservicio para gestion de polizas"
 │
 ▼
Kiro: Invoca get_required_inputs → te hace las preguntas necesarias
 │
 ▼
Tu: Respondes (nombre, entidades, BD, auth, etc.)
 │
 ▼
Kiro: Invoca get_project_plan → te muestra el plan de archivos
 │
 ▼
Tu: "Si, apruebo"
 │
 ▼
Kiro: Invoca initialize_project → MCP genera archivos en /repos/<proyecto>
 │
 ▼
Archivos aparecen en tu carpeta de repos local. Listo para docker compose up.
```

---

## Tools disponibles

| Tool | Descripcion |
|------|-------------|
| `list_available_stacks` | Lista los stacks de proyecto disponibles (java-spring-boot, node-express, python-fastapi) |
| `get_required_inputs` | Devuelve el schema de datos que el usuario debe proporcionar |
| `get_project_plan` | Genera el plan detallado de archivos (para confirmacion del usuario) |
| `initialize_project` | Ejecuta la generacion completa del proyecto en disco |
| `add_domain_module` | Agrega un modulo de dominio a un proyecto existente |
| `configure_infrastructure` | Actualiza la configuracion de infraestructura local |
| `get_blueprint` | Devuelve el blueprint tecnico como contexto para Kiro |
| `set_output_directory` | Configura el directorio base de salida (persiste entre sesiones) |

---

## Que genera

Un proyecto completo listo para `docker compose up`, segun el stack elegido:

### Java/Spring Boot
- **Gradle 9.x + Spring Boot 4.x + Java 21** con dependencias pinned
- **Estructura domain-driven** (controller/dto/service/repository por modulo)
- **Spring Security configurable** (OAuth2 RS, API Gateway, M2M, deferred)
- **Docker Compose local** (LocalStack SSM/S3/SQS + Mock OAuth + Datadog Agent no-forward)
- **SpringDoc OpenAPI + Swagger UI** funcional en local
- **CI/CD GitHub Actions** con templates institucionales
- **JaCoCo** con cobertura minima 85%

### Node.js/Express/TypeScript
- **Node.js 22 + Express 4.x + TypeScript 5.5+ strict**
- **Drizzle ORM** (PostgreSQL, type-safe)
- **Zod** para validacion runtime + tipos
- **Pino** para logging estructurado + AsyncLocalStorage (correlation-id)
- **Passport JWT** configurable (OAuth2 RS, API Gateway, M2M, deferred)
- **Vitest + Supertest** con cobertura minima 80%
- **ESLint v9 flat + Prettier + Husky** (opcional)
- **Docker multi-stage** (node:22-alpine)

### Python/FastAPI
- **Python 3.12 + FastAPI + uv** (package manager)
- **SQLAlchemy 2.x async** (asyncpg, PostgreSQL)
- **Pydantic v2** para validacion y settings
- **structlog** para logging estructurado + contextvars (correlation-id)
- **python-jose** para JWT (OAuth2 RS, M2M, deferred)
- **pytest + httpx** con cobertura minima 80%
- **Ruff** (lint + format + isort + bandit) + **mypy strict**
- **Docker multi-stage** (python:3.12-slim + uv)

### Comun a los 3 stacks
- **Docker Compose local** (LocalStack + Redis condicional + Mock OAuth condicional + Datadog Agent)
- **CI/CD GitHub Actions** con pipeline completo
- **Archivos .kiro** (steering, hooks, changelogs, mcp-settings)
- **README, api_spec.yaml, .env.sample** completos
- **4 auth strategies** pluggables (oauth2-resource-server, api-gateway-delegated, machine-to-machine, deferred)

---

## Donde colocar el mcp.json

| Ubicacion | Alcance | Cuando usar |
|-----------|---------|-------------|
| `~/.kiro/settings/mcp.json` | Todas las sesiones de Kiro | Tener el MCP disponible siempre |
| `<proyecto>/.kiro/settings/mcp.json` | Solo ese workspace | Solo en un proyecto especifico |

Si el archivo existe en ambos niveles, la configuracion del workspace tiene prioridad.

---

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| Kiro no detecta el MCP | Verificar que `mcp.json` esta en `.kiro/settings/mcp.json`. Reiniciar sesion. |
| "Cannot connect to Docker daemon" | Asegurar que Docker Desktop esta corriendo |
| "unauthorized" en pull de imagen | Verificar que el paquete ghcr.io esta marcado como **Public** en GitHub Package settings |
| "image not found" | Verificar nombre exacto de la imagen en el JSON |
| El MCP no responde | Reiniciar la sesion de Kiro (cierra y abre el chat) |
| Proyecto no aparece en disco | Verificar que el bind mount (`<TU_RUTA>:/repos`) apunta a la carpeta correcta. El path destino SIEMPRE es `:/repos`. |
| Archivos generados con permisos root | En Linux/Mac agregar `"--user", "$(id -u):$(id -g)"` a los args del JSON |
| Network timeout en build local | Usar `docker build --network=host` para acceso a internet desde el contenedor |
| "No se puede crear directorio" | El path debe estar dentro de `/repos` (el volumen montado). Verifica que tu bind mount termina en `:/repos` |
| MCP ejecuta version vieja | Verificar que `--pull always` esta en los args del mcp.json |
| Contenedor no arranca / no hay logs | Verificar que el bind mount termina en `:/repos` y NO en `:/` ni `:/workspace`. Montar en `/` destruye el filesystem del contenedor y lo mata inmediatamente. |

---

## Build local (solo si necesitas modificar el MCP)

> Esta seccion es para quienes contribuyen al desarrollo del MCP.
> Los usuarios finales NO necesitan hacer esto.

### Clonar y construir

```bash
git clone https://github.com/JohanMasmelaEu/MCP_INIT_MS_SegurosBolivar.git
cd MCP_INIT_MS_SegurosBolivar
docker build --network=host -t mcp-init-ms-segurosbolivar:latest .
```

> El flag `--network=host` es necesario para que el contenedor de build acceda a internet (PyPI). Sin esto, la red corporativa/VPN puede bloquear las conexiones.

### Usar la imagen local en Kiro

```json
{
  "mcpServers": {
    "MCP_INIT_MS_SegurosBolivar": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "<TU_RUTA_LOCAL>:/repos",
        "-v", "mcp-init-settings:/settings",
        "mcp-init-ms-segurosbolivar:latest"
      ],
      "disabled": false
    }
  }
}
```

La unica diferencia es el nombre de imagen: `mcp-init-ms-segurosbolivar:latest` (local) vs `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest` (registry).

> **Nota:** Para desarrollo local se omite `--pull always` porque la imagen ya esta construida localmente. Para produccion (imagen de registry) siempre incluir `--pull always`.

### Agregar un nuevo stack (futuro)

1. Crear directorio `templates/<nuevo-stack>/`
2. Agregar templates Jinja2 siguiendo la estructura existente
3. Crear `src/generators/<nuevo_stack>.py` extendiendo `BaseGenerator`
4. Registrar en `list_available_stacks`

---

## Publicar nueva version (para maintainers)

### Publicacion automatica (push a main)

Cada push a `main` dispara el workflow `.github/workflows/publish-image.yml` que:
1. Construye la imagen Docker
2. La publica en `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest`

### Publicar version con tag

```bash
git tag v1.1.0
git push origin v1.1.0
```

Genera tags en el registry: `1.1.0`, `1.1`, y actualiza `latest`.

### Configuracion inicial del pipeline (una sola vez)

1. GitHub repo → Settings → Actions → General
2. Workflow permissions: **"Read and write permissions"**
3. Marcar: **"Allow GitHub Actions to create and approve pull requests"**

### Hacer el paquete publico (una sola vez)

1. `https://github.com/users/JohanMasmelaEu/packages/container/mcp-init-ms-segurosbolivar/settings`
2. Danger Zone → Change package visibility → **Public**

Sin esto, los usuarios necesitarian autenticarse con Docker para hacer pull.

---

## Estructura del proyecto

```
MCP_INIT_MS_SegurosBolivar/
├── Dockerfile                      # Imagen Python 3.12 + MCP SDK
├── requirements.txt                # mcp, pydantic, jinja2, click
├── .github/workflows/
│   └── publish-image.yml           # CI: publica imagen en ghcr.io
├── src/
│   ├── server.py                   # Entry point MCP (stdio, 8 tools)
│   ├── tools/                      # Implementacion de cada tool
│   │   ├── set_output_directory.py # Configuracion persistente de salida
│   │   └── ...
│   ├── generators/                 # Logica de generacion por stack
│   ├── models/                     # Modelos Pydantic (config del proyecto)
│   └── utils/
│       ├── settings.py             # Persistencia de configuracion (/settings)
│       ├── file_writer.py          # Escritura segura de archivos
│       └── template_renderer.py    # Render Jinja2
├── templates/
│   ├── java-spring-boot/           # ~87 templates Jinja2 (Java 21 / Spring Boot 4.x)
│   ├── node-express/               # ~69 templates Jinja2 (Node 22 / Express / TypeScript)
│   └── python-fastapi/             # ~72 templates Jinja2 (Python 3.12 / FastAPI / uv)
│       ├── src/                    # Codigo fuente base: config, commons, middleware, errors, utils
│       ├── domain-module/          # Template repetible por cada modulo CRUD
│       ├── infra/                  # Dockerfile, docker-compose, LocalStack, Datadog
│       ├── cicd/                   # GitHub Actions, CODEOWNERS
│       ├── docs/                   # README, api_spec.yaml
│       ├── kiro/                   # .kiro steering, hooks, changelogs
│       └── git/                    # .gitignore, .gitattributes
├── blueprints/
│   ├── TECH_STACK_BLUEPRINT.md     # Blueprint Java
│   ├── TECH_STACK_BLUEPRINT_NODE.md # Blueprint Node
│   └── TECH_STACK_BLUEPRINT_PYTHON.md # Blueprint Python
└── rules/                          # Rules transversales inyectados en proyectos
```

---

## Volumenes Docker

| Volumen | Path interno | Tipo | Proposito |
|---------|--------------|------|-----------|
| `<TU_RUTA_LOCAL>:/repos` | `/repos` | Bind mount | Carpeta de repos del host. Aqui se generan los proyectos. |
| `mcp-init-settings:/settings` | `/settings` | Nombrado | Persiste configuracion del MCP (output directory). Sobrevive al `--rm`. |

> **NUNCA** montes el bind mount en `:/` ni en otro path que no sea `:/repos`. El contenedor depende de este path para funcionar correctamente.

El contenedor se ejecuta con `--rm` (se destruye al cerrar sesion), pero el volumen nombrado `mcp-init-settings` mantiene la configuracion entre ejecuciones.

---

## Restricciones de diseno

- No ejecuta nada sin mostrar plan al usuario primero
- No llama a LLMs externos (Kiro es el cerebro)
- No genera logica de negocio (solo estructura y boilerplate)
- No hardcodea secrets (solo placeholders + .env.sample)
- No toma decisiones de arquitectura (sigue el blueprint)

---

## Licencia

Uso interno Seguros Bolivar.
