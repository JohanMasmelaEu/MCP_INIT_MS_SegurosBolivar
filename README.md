# MCP_INIT_MS_SegurosBolivar

MCP Server para la inicializacion automatizada de microservicios en Seguros Bolivar. Genera arquetipos completos de proyectos Java 21 / Spring Boot 4.x / Gradle listos para desarrollo local con Docker Compose (LocalStack, Mock OAuth, Datadog Agent).

---

## Requisitos

- **Docker Desktop** instalado y corriendo (unico requisito de software)
- **Kiro IDE** (o cualquier cliente MCP compatible con transport stdio)

> **No se necesita Python, Java, ni ningun runtime instalado en la maquina.**
> Todo corre dentro del contenedor Docker.

---

## Instalacion y Configuracion

### Opcion A: Usar imagen pre-built (recomendado)

No necesitas clonar nada. Solo configura el MCP en Kiro:

Crear (o editar) el archivo `.kiro/settings/mcp.json` (en tu workspace o en `~/.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "MCP_INIT_MS_SegurosBolivar": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", ".:/workspace",
        "ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest"
      ],
      "disabled": false
    }
  }
}
```

Docker Desktop descarga la imagen automaticamente la primera vez. Listo.

### Opcion B: Build local (solo si necesitas modificar el MCP)

#### 1. Clonar el repositorio

```bash
git clone https://github.com/JohanMasmelaEu/MCP_INIT_MS_SegurosBolivar.git
cd MCP_INIT_MS_SegurosBolivar
```

#### 2. Construir la imagen Docker

```bash
docker build --network=host -t mcp-init-ms-segurosbolivar:latest .
```

> **Nota:** El flag `--network=host` es necesario para que el contenedor de build tenga acceso a internet (descarga dependencias de PyPI). Sin este flag, la red corporativa o VPN puede bloquear las conexiones salientes del contenedor.

#### 3. Configurar el MCP en Kiro (build local)

Crear (o editar) `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "MCP_INIT_MS_SegurosBolivar": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", ".:/workspace",
        "mcp-init-ms-segurosbolivar:latest"
      ],
      "disabled": false
    }
  }
}
```

> **Nota:** La unica diferencia con la Opcion A es el nombre de la imagen: `mcp-init-ms-segurosbolivar:latest` (local) vs `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest` (registry).

### 4. Usar el MCP (no requiere levantar nada manualmente)

El MCP **no se arranca por separado**. Kiro lo gestiona automaticamente:

1. Abre Kiro en el directorio donde quieres generar el proyecto
2. Kiro detecta el `mcp.json` al iniciar la sesion
3. Internamente ejecuta `docker run -i --rm ...` y mantiene la conexion via stdio
4. El contenedor vive mientras la sesion de Kiro este activa
5. Al cerrar la sesion, el contenedor se destruye automaticamente (`--rm`)

**Para verificar que funciona**, abre una sesion en Kiro y escribe:

> "Lista los stacks disponibles del MCP de inicializacion"

Kiro invocara `list_available_stacks` y deberia responder con `java-spring-boot`.

### Troubleshooting

| Problema | Solucion |
|----------|----------|
| Kiro no detecta el MCP | Verificar que `mcp.json` esta en `.kiro/settings/mcp.json` (workspace o global) |
| "Cannot connect to Docker daemon" | Asegurar que Docker Desktop esta corriendo |
| "image not found" | Ejecutar el build del paso 2 |
| El MCP no responde | Reiniciar la sesion de Kiro (cierra y abre el chat) |
| Archivos generados con permisos root | En Linux/Mac agregar `"--user", "$(id -u):$(id -g)"` a los args |

---

## Como funciona el enlace MCP ↔ Kiro

### Arquitectura de comunicacion

```
┌─────────────────────────────────────────────────────────────────┐
│  Kiro IDE (tu maquina)                                          │
│                                                                 │
│  1. Lee .kiro/settings/mcp.json                                 │
│  2. Ejecuta: docker run -i --rm -v <workspace>:/workspace ...   │
│  3. Conecta al proceso via stdio (stdin/stdout)                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Contenedor Docker (mcp-init-ms-segurosbolivar:latest)    │  │
│  │                                                           │  │
│  │  Python 3.12 + MCP SDK                                    │  │
│  │  ├── Recibe llamadas JSON-RPC via stdin                   │  │
│  │  ├── Ejecuta tools (get_project_plan, initialize, etc.)   │  │
│  │  ├── Escribe archivos en /workspace (volumen montado)     │  │
│  │  └── Responde resultados via stdout                       │  │
│  │                                                           │  │
│  │  /workspace ← montado desde tu directorio local           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  4. Kiro recibe respuestas y las presenta al usuario            │
│  5. Al cerrar sesion → contenedor se destruye (--rm)            │
└─────────────────────────────────────────────────────────────────┘
```

### Protocolo MCP (Model Context Protocol)

MCP es un protocolo estandar que permite a LLMs (como Kiro/Claude) invocar herramientas externas de forma estructurada. En este caso:

- **Transport:** `stdio` — Kiro se comunica con el contenedor Docker via stdin/stdout
- **Protocolo:** JSON-RPC 2.0 sobre stdio
- **Lifecycle:**
  1. Kiro inicia sesion → lee `mcp.json` → arranca el contenedor
  2. Handshake: Kiro pregunta que tools tiene el MCP → el MCP responde con la lista
  3. Kiro sabe que tools tiene disponibles y los usa segun el contexto de la conversacion
  4. Cada invocacion: Kiro envia JSON-RPC request → MCP ejecuta → responde JSON-RPC response
  5. Cierre: Kiro termina sesion → stdin se cierra → contenedor sale → Docker lo elimina

### Donde colocar el mcp.json

| Ubicacion | Alcance | Cuando usar |
|-----------|---------|-------------|
| `<proyecto>/.kiro/settings/mcp.json` | Solo ese workspace | Si solo quieres el MCP en un proyecto especifico |
| `~/.kiro/settings/mcp.json` | Todas las sesiones de Kiro | Si quieres tener el MCP disponible siempre |

Si el archivo existe en ambos niveles, la configuracion del workspace tiene prioridad.

### Que pasa internamente cuando hablas con Kiro

```
Tu: "Inicializa un microservicio para gestion de polizas"
 │
 ▼
Kiro (LLM): Interpreta tu peticion → decide invocar get_required_inputs
 │
 ▼
Kiro → Docker (stdin): {"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_required_inputs","arguments":{"stack":"java-spring-boot"}}}
 │
 ▼
MCP Server (Python): Ejecuta la funcion → retorna schema de preguntas
 │
 ▼
Docker → Kiro (stdout): {"jsonrpc":"2.0","result":{"content":[{"text":"...schema JSON..."}]}}
 │
 ▼
Kiro (LLM): Procesa el schema → te hace las preguntas necesarias
 │
 ▼
Tu: Respondes las preguntas
 │
 ▼
Kiro: Arma la config completa → invoca get_project_plan → te muestra el plan
 │
 ▼
Tu: "Si, apruebo"
 │
 ▼
Kiro: Invoca initialize_project → MCP escribe archivos en /workspace (tu directorio)
 │
 ▼
Archivos aparecen en tu directorio local (porque /workspace es un volumen montado)
```

### Verificar que el MCP esta conectado

En Kiro, abre el panel de funciones MCP (Command Palette → "MCP") para ver los servidores activos. `MCP_INIT_MS_SegurosBolivar` deberia aparecer con estado "running" y 7 tools listados.

---

## Uso

### Flujo tipico

1. **Abre Kiro** en un directorio vacio (o donde quieras generar el proyecto)
2. **Dile a Kiro:** "Quiero inicializar un nuevo microservicio para gestion de [tu dominio]"
3. **Kiro te preguntara** los datos necesarios (nombre, entidades, BD, auth, etc.)
4. **Kiro te mostrara el plan** de archivos a generar
5. **Confirmas** y el MCP genera todo el proyecto
6. **Levantas** con `docker compose up` desde `development/docker-local-ms/`

### Tools disponibles

| Tool | Descripcion |
|------|-------------|
| `list_available_stacks` | Lista los stacks de proyecto disponibles (V1: java-spring-boot) |
| `get_required_inputs` | Devuelve el schema de datos que el usuario debe proporcionar |
| `get_project_plan` | Genera el plan detallado de archivos (para confirmacion) |
| `initialize_project` | Ejecuta la generacion completa del proyecto |
| `add_domain_module` | Agrega un modulo de dominio a un proyecto existente |
| `configure_infrastructure` | Actualiza la configuracion de infraestructura local |
| `get_blueprint` | Devuelve el blueprint tecnico como contexto |

---

## Que genera

Un proyecto completo con:

- Gradle 9.x + Spring Boot 4.x + Java 21
- Estructura domain-driven (controller/dto/service/repository por modulo)
- Spring Security configurable (OAuth2 RS, API Gateway, deferred)
- Docker Compose local (LocalStack SSM/S3/SQS + Mock OAuth + Datadog Agent)
- SpringDoc OpenAPI + Swagger UI funcional en local
- CI/CD GitHub Actions con templates institucionales
- JaCoCo con cobertura minima 85%
- Archivos de contexto .kiro (steering, rules, changelogs)
- README, Postman template, api_spec.yaml base

---

## Estructura del MCP

```
MCP_INIT_MS_SegurosBolivar/
├── Dockerfile
├── requirements.txt
├── README.md
├── src/
│   ├── server.py              # Entry point MCP (stdio)
│   ├── tools/                 # Implementacion de cada tool
│   ├── generators/            # Logica de generacion por stack
│   ├── models/                # Modelos Pydantic (input del usuario)
│   └── utils/                 # Template renderer, file writer
├── templates/
│   └── java-spring-boot/      # Templates Jinja2 del arquetipo
├── blueprints/                # TECH_STACK_BLUEPRINT.md
└── rules/                     # Rules transversales a inyectar
```

---

## Desarrollo del MCP (solo para contribuidores)

> Esta seccion es SOLO para quienes modifican el MCP en si.
> Los usuarios finales NO necesitan Python instalado — todo corre via Docker.

### Correr sin Docker (solo desarrollo del MCP)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m src.server
```

### Agregar un nuevo stack (futuro)

1. Crear directorio `templates/<nuevo-stack>/`
2. Agregar templates Jinja2 siguiendo la estructura
3. Crear `src/generators/<nuevo_stack>.py` extendiendo `BaseGenerator`
4. Registrar en `list_available_stacks`

---

## Restricciones de diseno

- No ejecuta nada sin mostrar plan al usuario primero
- No llama a LLMs externos (Kiro es el cerebro)
- No genera logica de negocio (solo estructura y boilerplate)
- No hardcodea secrets (solo placeholders + .env.sample)
- No toma decisiones de arquitectura (sigue el blueprint)

---

## Publicar la imagen (para maintainers)

La imagen se publica automaticamente en GitHub Container Registry (ghcr.io) via GitHub Actions. Paso a paso:

### 1. Configurar permisos del repositorio (una sola vez)

1. Ve a tu repo en GitHub: `https://github.com/JohanMasmelaEu/MCP_INIT_MS_SegurosBolivar`
2. Settings → Actions → General
3. En "Workflow permissions" selecciona **"Read and write permissions"**
4. Marca **"Allow GitHub Actions to create and approve pull requests"**
5. Guarda

### 2. Hacer push a main

```bash
cd MCP_INIT_MS_SegurosBolivar
git add .
git commit -m "feat: MCP server v1.0.0 - inicializacion de microservicios Java/Spring Boot"
git push origin main
```

El workflow `publish-image.yml` se dispara automaticamente y:
- Construye la imagen Docker
- La publica en `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest`

### 3. Verificar que la imagen se publico

- Ve a: `https://github.com/JohanMasmelaEu/MCP_INIT_MS_SegurosBolivar/pkgs/container/mcp-init-ms-segurosbolivar`
- O en la tab "Packages" de tu perfil de GitHub

### 4. Hacer la imagen publica (una sola vez)

Por defecto, las imagenes en ghcr.io heredan la visibilidad del repo. Si el repo es publico, la imagen es publica. Si es privado:

1. Ve a: `https://github.com/users/JohanMasmelaEu/packages/container/mcp-init-ms-segurosbolivar/settings`
2. En "Danger Zone" → "Change package visibility" → selecciona **Public**
3. Confirma

Esto permite que cualquier usuario con Docker Desktop haga `docker pull` sin autenticarse.

### 5. Publicar una version con tag (opcional)

Para publicar una version especifica (ej: v1.0.0):

```bash
git tag v1.0.0
git push origin v1.0.0
```

Esto genera tags adicionales en el registry:
- `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:1.0.0`
- `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:1.0`
- `ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest`

### 6. Verificar desde cualquier maquina

```bash
docker pull ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest
docker run -i --rm ghcr.io/johanmasmelaeu/mcp-init-ms-segurosbolivar:latest
```

Si responde el handshake JSON-RPC, funciona.

---

## Licencia

Uso interno Seguros Bolivar.
