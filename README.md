# MCP_INIT_MS_SegurosBolivar

MCP Server para la inicializacion automatizada de microservicios en Seguros Bolivar. Genera arquetipos completos de proyectos Java 21 / Spring Boot 4.x / Gradle listos para desarrollo local con Docker Compose (LocalStack, Mock OAuth, Datadog Agent).

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
        "-v", "C:/REPOS:/repos",
        "-v", "mcp-init-settings:/settings",
        "ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest"
      ],
      "disabled": false
    }
  }
}
```

**Importante:** Reemplaza `C:/REPOS` con la ruta de tu carpeta raiz de repositorios.

| Volumen | Proposito | Tipo |
|---------|-----------|------|
| `C:/REPOS:/repos` | Tu carpeta de repos mapeada dentro del contenedor. Los proyectos generados se escriben aqui. | Bind mount |
| `mcp-init-settings:/settings` | Persiste la configuracion del MCP (directorio de salida) entre sesiones. | Volumen nombrado |

> **Esta es la unica configuracion que necesitas hacer.** Una vez configurado, nunca mas se modifica.

### 2. Reiniciar sesion de Kiro

Cierra y abre el chat en Kiro para que lea la nueva configuracion.
Docker Desktop descargara la imagen automaticamente la primera vez (~150MB).

### 3. Verificar

Escribe en Kiro:

> "Lista los stacks disponibles del MCP de inicializacion"

Deberia responder con `java-spring-boot`. Si lo hace, el MCP esta funcionando.

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

| Dentro del contenedor | En tu maquina (si montaste `C:/REPOS:/repos`) |
|-----------------------|------------------------------------------------|
| `/repos` | `C:\REPOS` |
| `/repos/SegurosBolivar` | `C:\REPOS\SegurosBolivar` |
| `/repos/SegurosBolivar/mi-ms` | `C:\REPOS\SegurosBolivar\mi-ms` |

El MCP siempre trabaja con rutas `/repos/...` internamente. Kiro traduce automaticamente en la conversacion.

---

## Como funciona

### Arquitectura de comunicacion

```
┌─────────────────────────────────────────────────────────────────┐
│  Kiro IDE (tu maquina)                                          │
│                                                                 │
│  1. Lee .kiro/settings/mcp.json                                 │
│  2. Ejecuta: docker run -i --rm -v C:/REPOS:/repos              │
│     -v mcp-init-settings:/settings <imagen>                     │
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
│  │  /repos ← bind mount desde C:/REPOS                       │  │
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
| `list_available_stacks` | Lista los stacks de proyecto disponibles (V1: java-spring-boot) |
| `get_required_inputs` | Devuelve el schema de datos que el usuario debe proporcionar |
| `get_project_plan` | Genera el plan detallado de archivos (para confirmacion del usuario) |
| `initialize_project` | Ejecuta la generacion completa del proyecto en disco |
| `add_domain_module` | Agrega un modulo de dominio a un proyecto existente |
| `configure_infrastructure` | Actualiza la configuracion de infraestructura local |
| `get_blueprint` | Devuelve el blueprint tecnico como contexto para Kiro |
| `set_output_directory` | Configura el directorio base de salida (persiste entre sesiones) |

---

## Que genera

Un proyecto completo listo para `docker compose up`:

- **Gradle 9.x + Spring Boot 4.x + Java 21** con dependencias pinned
- **Estructura domain-driven** (controller/dto/service/repository por modulo)
- **Spring Security configurable** (OAuth2 RS, API Gateway, deferred)
- **Docker Compose local** (LocalStack SSM/S3/SQS + Mock OAuth + Datadog Agent no-forward)
- **SpringDoc OpenAPI + Swagger UI** funcional en local
- **CI/CD GitHub Actions** con templates institucionales
- **JaCoCo** con cobertura minima 85%
- **Archivos .kiro** (steering, rules, changelogs) para contexto de Kiro
- **README, api_spec.yaml, .env.sample** completos

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
| Proyecto no aparece en disco | Verificar que el bind mount (`C:/REPOS:/repos`) apunta a la carpeta correcta |
| Archivos generados con permisos root | En Linux/Mac agregar `"--user", "$(id -u):$(id -g)"` a los args del JSON |
| Network timeout en build local | Usar `docker build --network=host` para acceso a internet desde el contenedor |
| "No se puede crear directorio" | El path debe estar dentro de `/repos` (el volumen montado) |

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
        "-v", "C:/REPOS:/repos",
        "-v", "mcp-init-settings:/settings",
        "mcp-init-ms-segurosbolivar:latest"
      ],
      "disabled": false
    }
  }
}
```

La unica diferencia es el nombre de imagen: `mcp-init-ms-segurosbolivar:latest` (local) vs `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest` (registry).

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
│   └── java-spring-boot/           # 63 templates Jinja2 del arquetipo
│       ├── gradle/                 # build.gradle, wrapper, settings
│       ├── src/                    # Java base: commons, config, entity, errorhandling, utils
│       ├── domain-module/          # Template repetible por cada modulo CRUD
│       ├── resources/              # application.yaml (3 perfiles)
│       ├── infra/                  # Dockerfile, docker-compose, LocalStack, Datadog
│       ├── cicd/                   # GitHub Actions, CODEOWNERS
│       ├── docs/                   # README, api_spec.yaml
│       ├── kiro/                   # .kiro steering, changelogs
│       └── git/                    # .gitignore, .gitattributes
├── blueprints/                     # TECH_STACK_BLUEPRINT.md
└── rules/                          # Rules transversales inyectados en proyectos
```

---

## Volumenes Docker

| Volumen | Path interno | Tipo | Proposito |
|---------|--------------|------|-----------|
| `C:/REPOS:/repos` | `/repos` | Bind mount | Carpeta de repos del host. Aqui se generan los proyectos. |
| `mcp-init-settings:/settings` | `/settings` | Nombrado | Persiste configuracion del MCP (output directory). Sobrevive al `--rm`. |

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
