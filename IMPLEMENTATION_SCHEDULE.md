# Schedule de Implementación — MCP_INIT_MS_SegurosBolivar

## Contexto para el agente ejecutor

**Qué es este proyecto:** Un MCP Server (Model Context Protocol) en Python que genera proyectos backend (microservicios Java/Spring Boot) para Seguros Bolívar. Se ejecuta como container Docker y Kiro IDE lo consume via stdio.

**Qué hay que hacer:** Actualizar el output que genera el MCP cuando crea un proyecto. Actualmente genera una carpeta `.kiro/` mínima (1 steering + 4 hooks). Debe pasar a generar la estructura completa definida en `CONSOLIDADO_DISENO_MCP.md`.

**Archivos clave del proyecto:**
- `src/models/project_config.py` — Modelo Pydantic con la configuración del proyecto
- `src/generators/java_spring_boot.py` — Generador principal, método `_generate_kiro_context()`
- `src/tools/get_required_inputs.py` — Schema de inputs que se le pide al usuario
- `src/tools/get_project_plan.py` — Preview del file tree antes de generar
- `templates/java-spring-boot/kiro/` — Templates Jinja2 que generan los archivos .kiro/
- `CONSOLIDADO_DISENO_MCP.md` — Documento de diseño con TODO el contenido de cada archivo

**Convenciones de templates:**
- Los templates usan Jinja2 con extensión `.j2`
- Variables disponibles en contexto: `config` (ProjectConfig), `c` (alias), `modules`, `project_name`, etc.
- Filtros custom: `to_camel_case`, `to_pascal_case`, `to_snake_case`, `to_upper_snake`, `pluralize_es`

---

## TAREAS (ejecutar en orden)

### TASK 1 — Actualizar el modelo ProjectConfig

**Archivo:** `src/models/project_config.py`

**Qué hacer:** Agregar 3 campos opcionales al modelo `ProjectConfig`:

```python
# Agregar después del campo selected_mcps:

# --- Metadatos adicionales del proyecto ---
i18n: list[str] = Field(
    default_factory=lambda: ["es"],
    description="Idiomas activos para mensajes (es, en). Default solo español.",
)
cache: Optional[str] = Field(
    default=None,
    description="Tecnología de cache si aplica (ej: 'redis'). None = sin cache.",
)
docker_profile: Optional[str] = Field(
    default=None,
    description="Perfil de imagen Docker (ej: 'java-redis'). Define qué incluye la imagen.",
)
```

**Validación:** El archivo debe seguir importando `Optional` de typing (ya lo importa). No se requieren validators adicionales.

**Criterio de done:** `ProjectConfig(project_name="test-ms", context_path="/test", api_description="test", database=DatabaseConfig(db_name="x", db_user="x", db_password="x"))` debe instanciarse sin error con los nuevos campos en sus defaults.

---

### TASK 2 — Crear template project.json.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/project.json.j2`

**Contenido exacto:**

```jinja2
{
  "stack": "java",
  "dockerProfile": {{ (c.docker_profile or "java-standard") | tojson }},
  "cache": {{ (c.cache or "none") | tojson }},
  "i18n": {{ c.i18n | tojson }},
  "generatedBy": "mcp-init-ms-segurosbolivar",
  "createdAt": "{{ now_iso }}"
}
```

**Nota:** La variable `now_iso` debe agregarse al contexto del generador (ver Task 14). Si no está disponible, usar un string estático como `"2026-01-01"` como placeholder y dejarlo como TODO.

**Criterio de done:** El archivo existe en la ruta indicada y es Jinja2 válido.

---

### TASK 3 — Crear template steering 00-org-conventions.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/00-org-conventions.md.j2`

**Contenido:** Extraer la sección completa `### 00-org-conventions.md` del archivo `CONSOLIDADO_DISENO_MCP.md` y convertirla en un template Jinja2. Las partes dinámicas son:

- `{{ project_name }}` donde se mencione el nombre del proyecto
- `{{ context_path }}` donde se mencione el context path
- `{% for module in modules %}` si hay listas de módulos

**Sin embargo**, este steering es mayormente texto estático (convenciones organizacionales). No necesita variables Jinja2 salvo un header informativo:

```jinja2
---
inclusion: always
---
# Convenciones Organizacionales — {{ project_name }}

> Generado por MCP_INIT_MS_SegurosBolivar. No editar manualmente.

[COPIAR TODO EL CONTENIDO DE LA SECCIÓN 00-org-conventions.md DEL CONSOLIDADO]
```

**Instrucción clave:** El contenido completo de esta sección está en `CONSOLIDADO_DISENO_MCP.md`, sección "### `00-org-conventions.md`". Copiarlo íntegro como cuerpo del template, solo agregando el front-matter de Kiro (`inclusion: always`) y el header con `{{ project_name }}`.

**Criterio de done:** El archivo existe, tiene front-matter `inclusion: always`, y contiene las reglas de URLs, verbos HTTP, naming, idioma, lineamientos, documentación, backward compatibility, i18n, contenerización, cache, config por ambiente, y postman collections.

---

### TASK 4 — Crear template steering 01-architecture.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/01-architecture.md.j2`

**Instrucción:** Mismo patrón que Task 3. Extraer sección "### `01-architecture.md`" del consolidado. Front-matter `inclusion: always`. Header con `{{ project_name }}`. El contenido incluye: estructura del código, reglas de estructura, contrato entre dominios, resiliencia, concurrencia/transacciones, API First, ownership schema, governance, connection pooling, file upload.

**Parte dinámica:** La estructura de ejemplo puede mostrar los módulos reales del proyecto:
```jinja2
{% for module in modules %}
└── {{ module.module_name }}/
    ├── controller/
    ├── dto/
    ├── services/
    └── repository/
{% endfor %}
```

**Criterio de done:** Archivo existe con todo el contenido de arquitectura del consolidado.

---

### TASK 5 — Crear template steering 02-security.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/02-security.md.j2`

**Instrucción:** Extraer sección "### `02-security.md`" del consolidado. 100% texto estático (no depende del proyecto). Front-matter `inclusion: always`. Sin variables Jinja2 necesarias.

**Criterio de done:** Archivo existe con todas las reglas de seguridad: Zero Trust, inyección, SSRF, path traversal, auth, BOLA/IDOR, headers, secrets, information leakage, dependencias.

---

### TASK 6 — Crear template steering 03-code-style.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/03-code-style.md.j2`

**Instrucción:** Extraer sección "### `03-code-style.md`" del consolidado. 100% texto estático. Front-matter `inclusion: always`. Incluye: principios, funciones, type safety, naming, imports, dead code, documentación, SonarQube, Trash to Delete Trash.

**Criterio de done:** Archivo existe con tabla de severidades (bloquea/requiere justificación/recomendación) y la descripción del Trash Inspector como herramienta auxiliar.

---

### TASK 7 — Crear template steering 04-testing-standards.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/04-testing-standards.md.j2`

**Instrucción:** Extraer sección "### `04-testing-standards.md`" del consolidado. Front-matter `inclusion: always`. Texto mayormente estático. Incluye tabla de frameworks por stack.

**Criterio de done:** Archivo existe con regla de 80% coverage, patrón Given/When/Then, tabla de frameworks, exclusiones.

---

### TASK 8 — Crear template steering 05-responsible-ai-use.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/05-responsible-ai-use.md.j2`

**Instrucción:** Extraer sección "### `05-responsible-ai-use.md`" del consolidado. 100% texto estático. Front-matter `inclusion: always`. Este es el steering MÁS IMPORTANTE — contiene:
- Plan dos niveles (ligero/completo) con tabla de criterio determinístico
- Validación de prompt (acción + objeto)
- Override con confirmación
- Adherencia absoluta a la arquitectura (tabla prohibido/permitido)
- Reglas de AI-generated code

**Criterio de done:** Archivo existe con toda la tabla de adherencia y las reglas de plan.

---

### TASK 9 — Crear template steering 06-data-access.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/06-data-access.md.j2`

**Instrucción:** Extraer sección "### `06-data-access.md`" del consolidado. 100% estático. Front-matter `inclusion: always`. Incluye: ORM obligatorio (tabla por stack), prohibido, obligatorio, SQL raw escape hatch.

**Criterio de done:** Archivo existe con tabla de ORM por stack y reglas de paginación/N+1.

---

### TASK 10 — Crear template steering 07-error-handling.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/07-error-handling.md.j2`

**Instrucción:** Extraer sección "### `07-error-handling.md`" del consolidado. 100% estático. Front-matter `inclusion: always`. Incluye: principio (500=bug), obligatorio, prohibido, formato error JSON, tabla de capas.

**Criterio de done:** Archivo existe con formato de error estándar y tabla de responsabilidad por capa.

---

### TASK 11 — Crear template steering 08-observability.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/08-observability.md.j2`

**Instrucción:** Extraer sección "### `08-observability.md`" del consolidado. 100% estático. Front-matter `inclusion: always`. Incluye: nota de alcance Java-specific, tabla por ambiente, correlation ID, masking, niveles, prohibido, contrato cross-stack.

**Criterio de done:** Archivo existe con tabla de ambientes (local/prod/soporte) y nota de alcance.

---

### TASK 12 — Crear template steering 10-stack-java.md.j2

**Archivo a crear:** `templates/java-spring-boot/kiro/steering/10-stack-java.md.j2`

**Instrucción:** Extraer sección "### `10-stack-java.md`" del consolidado. Front-matter con inclusión condicional:

```yaml
---
inclusion: always
---
```

(Se usa `always` porque este template SOLO se genera en proyectos Java — la condicionalidad está en que el MCP solo lo genera para stack java, no en el front-matter de Kiro).

Contenido: tabla de componentes Java (JDK 21, Gradle 9.4, Spring Boot 4.0, etc.).

**Criterio de done:** Archivo existe con tabla completa del stack Java.

---

### TASK 13 — Crear templates de hooks

**Directorio:** `templates/java-spring-boot/kiro/hooks/`

**Acción:** ELIMINAR los 4 hooks actuales y crear 7 nuevos:

**Archivos a eliminar:**
- `code-standards-check.json.j2`
- `compile-on-save.json.j2`
- `security-review.json.j2`
- `test-after-task.json.j2`

**Archivos a crear (contenido exacto para cada uno):**

#### 13.1 — `pre-write-gate.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Pre-write Gate — Plan + Arquitectura + Calidad",
      "trigger": "PreToolUse",
      "matcher": "fs_write|str_replace|fs_append",
      "action": {
        "type": "agent",
        "prompt": "Antes de escribir este codigo, evalua:\n\n1. PLAN: Declara en 1-2 lineas que vas a hacer (plan ligero). Si el cambio cumple alguna de estas condiciones: (a) diff > 15 lineas, (b) mas de 1 archivo tocado, (c) toca dto/, schema/, model, config/, auth/ — entonces presenta plan COMPLETO (archivos, logica, tests, errores posibles) y ESPERA confirmacion del usuario.\n\n2. ARQUITECTURA: Verifica que lo que vas a implementar es consistente con la estructura del proyecto existente (organizacion por dominio, patrones, naming). Si vas a divergir, DETENTE y pregunta.\n\n3. SCOPE: Verifica que agregas SOLO lo que el usuario pidio. No extras, no features bonus, no refactorizaciones no solicitadas.\n\nSi ya se aprobo un plan para este modulo en la sesion actual, no re-preguntar."
      }
    }
  ]
}
```

#### 13.2 — `responsible-use.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Validacion de prompt — accion + objeto",
      "trigger": "UserPromptSubmit",
      "action": {
        "type": "agent",
        "prompt": "Evalua si el prompt del usuario contiene: (a) una accion reconocible (crear, agregar, corregir, refactorizar, eliminar, actualizar) Y (b) un objeto/entidad concreto (endpoint, servicio, DTO, dominio, campo, etc.).\n\nSi AMBOS estan presentes: procede sin preguntar nada, sin importar lo breve del prompt.\nSi FALTA alguno: pregunta especificamente que falta. No pidas 'elaborar mas' de forma generica — pregunta puntual: '¿A que dominio pertenece?' o '¿Que accion necesitas sobre ese recurso?'"
      }
    }
  ]
}
```

#### 13.3 — `code-review-gate.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Review post-escritura",
      "trigger": "PostToolUse",
      "matcher": "fs_write|str_replace|fs_append",
      "action": {
        "type": "agent",
        "prompt": "Codigo escrito. Recuerda al usuario verificar:\n- Naming correcto segun convenciones (Controller, Service, ServiceImpl, Request, Response)\n- Error handling presente (no dejar caminos sin captura)\n- Tests necesarios para esta implementacion\n- Consistencia con la arquitectura del proyecto\n- No hay codigo basura (imports no usados, console.log, TODO sin resolver)"
      }
    }
  ]
}
```

#### 13.4 — `test-coverage-gate.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Verificacion de tests al completar tarea",
      "trigger": "PostTaskExec",
      "action": {
        "type": "agent",
        "prompt": "Tarea completada. Verifica:\n1. ¿Se crearon/actualizaron archivos de test correspondientes al codigo nuevo?\n2. ¿Los tests cubren el happy path Y los caminos de error?\n3. ¿El patron es Given/When/Then?\n\nSi no hay tests para el codigo nuevo, informa al usuario: 'No se detectan tests para este cambio. El estandar requiere 80% coverage. ¿Quieres que los genere ahora o prefieres continuar sin ellos?'"
      }
    }
  ]
}
```

#### 13.5 — `build-validate.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Compilar al guardar archivo Java",
      "trigger": "PostFileSave",
      "matcher": "\\.java$",
      "action": {
        "type": "command",
        "command": "./gradlew compileJava --daemon -q"
      }
    }
  ]
}
```

#### 13.6 — `integrity-check.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Verificacion de integridad al inicio de sesion",
      "trigger": "SessionStart",
      "action": {
        "type": "agent",
        "prompt": "Inicio de sesion. Verifica que los hooks criticos del proyecto existen:\n- .kiro/hooks/pre-write-gate.json\n- .kiro/hooks/responsible-use.json\n\nSi alguno falta, informa al usuario: '⚠️ Hook [nombre] no esta activo. Los cambios no pasaran por confirmacion automatica — operando en modo degradado.'\n\nNo bloquees la sesion. Solo informa y continua. Aplica las reglas de los steering files como fallback de autoevaluacion."
      }
    }
  ]
}
```

#### 13.7 — `summary-on-completion.json.j2`
```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Resumen al finalizar sesion",
      "trigger": "Stop",
      "action": {
        "type": "agent",
        "prompt": "Sesion finalizada. Presenta al usuario:\n1. Resumen de archivos creados/modificados en esta sesion\n2. Si hubo cambios significativos, sugiere ejecutar el Trash Inspector\n3. Pide validacion: '¿Los cambios son correctos? ¿Hay algo que ajustar antes de cerrar?'"
      }
    }
  ]
}
```

**Criterio de done:** Los 4 archivos viejos eliminados, los 7 nuevos creados con el contenido exacto indicado arriba.

---

### TASK 14 — Actualizar el generador para producir la nueva estructura .kiro/

**Archivo:** `src/generators/java_spring_boot.py`

**Método a modificar:** `_generate_kiro_context()`

**Estado actual del método (reemplazar completamente):**
```python
def _generate_kiro_context(self) -> None:
    """Genera archivos de contexto .kiro/ (steering, changelogs, hooks, mcp, specs)."""
    self._render_write("kiro/api-context.md.j2", ".kiro/steering/api-context.md")
    self._render_write("kiro/changelog-develop.md.j2", ".kiro/changelogs/changelog-develop.md")
    # ... (hay más líneas después que copian rules)
```

**Nuevo contenido del método:**
```python
def _generate_kiro_context(self) -> None:
    """Genera archivos .kiro/ completos: project.json, steering, hooks, changelogs, mcp."""
    from datetime import date

    # Agregar fecha al contexto
    ctx_with_date = {**self.ctx, "now_iso": date.today().isoformat()}

    # project.json — metadato del proyecto
    self._render_write("kiro/project.json.j2", ".kiro/project.json", ctx_with_date)

    # Steering files (convenciones y reglas)
    steering_files = [
        "00-org-conventions",
        "01-architecture",
        "02-security",
        "03-code-style",
        "04-testing-standards",
        "05-responsible-ai-use",
        "06-data-access",
        "07-error-handling",
        "08-observability",
        "10-stack-java",
    ]
    for name in steering_files:
        self._render_write(
            f"kiro/steering/{name}.md.j2",
            f".kiro/steering/{name}.md",
            ctx_with_date,
        )

    # Hooks
    hook_files = [
        "pre-write-gate",
        "responsible-use",
        "code-review-gate",
        "test-coverage-gate",
        "build-validate",
        "integrity-check",
        "summary-on-completion",
    ]
    for name in hook_files:
        self._render_write(
            f"kiro/hooks/{name}.json.j2",
            f".kiro/hooks/{name}.json",
        )

    # Changelog
    self._render_write("kiro/changelog-develop.md.j2", ".kiro/changelogs/changelog-develop.md")

    # MCP settings (si hay MCPs seleccionados)
    if self.config.selected_mcps:
        self._render_write("kiro/mcp-settings.json.j2", ".kiro/settings/mcp.json")
```

**También modificar `_build_context()`** para incluir los nuevos campos:
```python
# Agregar al diccionario retornado por _build_context():
"i18n": self.config.i18n,
"cache": self.config.cache,
"docker_profile": self.config.docker_profile,
```

**Criterio de done:** El método genera project.json + 10 steering files + 7 hooks + changelog + mcp settings. No genera el viejo `api-context.md`.

---

### TASK 15 — Actualizar get_required_inputs con nuevos campos

**Archivo:** `src/tools/get_required_inputs.py`

**Qué hacer:** Agregar una nueva categoría al final de la lista de categorías (antes del return):

```python
def _project_metadata_category() -> dict:
    """Categoria: metadatos adicionales del proyecto."""
    return {
        "name": "project_metadata",
        "label": "Metadatos del Proyecto",
        "description": "Configuracion adicional para i18n, cache y contenedorizacion.",
        "fields": [
            {
                "key": "i18n",
                "label": "Idiomas activos para mensajes",
                "type": "array",
                "required": False,
                "default": ["es"],
                "example": ["es", "en"],
                "description": "Idiomas para mensajes de error/validacion. Default: solo español.",
            },
            {
                "key": "cache",
                "label": "Tecnologia de cache (opcional)",
                "type": "string",
                "required": False,
                "default": None,
                "options": [
                    {"value": "redis", "description": "Redis como cache distribuido"},
                    {"value": None, "description": "Sin cache"},
                ],
            },
            {
                "key": "docker_profile",
                "label": "Perfil de imagen Docker",
                "type": "string",
                "required": False,
                "default": "java-standard",
                "description": "Define que incluye la imagen Docker. Se indexa en project.json.",
                "example": "java-redis",
            },
        ],
    }
```

Y agregarla a la lista de categorías en `handle_get_required_inputs`:
```python
"categories": [
    _project_identity_category(),
    _domain_modules_category(),
    _database_category(),
    _authentication_category(),
    _integrations_category(),
    _observability_category(),
    _artifactory_category(),
    _mcp_marketplace_category(),
    _project_metadata_category(),  # NUEVA
],
```

**Criterio de done:** Llamar a `handle_get_required_inputs("java-spring-boot")` retorna 9 categorías (antes eran 8).

---

### TASK 16 — Actualizar get_project_plan para reflejar nueva estructura .kiro/

**Archivo:** `src/tools/get_project_plan.py`

**Qué hacer:** En la función `_build_file_tree()`, reemplazar la sección `# --- Kiro context ---` (actualmente 2 entradas) con la nueva lista completa:

```python
# --- Kiro context ---
files.extend([
    _file(f"{p}/.kiro/project.json", "Metadato del proyecto: stack, cache, i18n, dockerProfile"),
    _file(f"{p}/.kiro/steering/00-org-conventions.md", "Convenciones organizacionales: URLs, naming, idioma, docs"),
    _file(f"{p}/.kiro/steering/01-architecture.md", "Arquitectura backend: dominios, contratos, resiliencia"),
    _file(f"{p}/.kiro/steering/02-security.md", "Seguridad: Zero Trust, inyeccion, headers, secrets"),
    _file(f"{p}/.kiro/steering/03-code-style.md", "Codigo limpio: SOLID, funciones, Trash Inspector"),
    _file(f"{p}/.kiro/steering/04-testing-standards.md", "Testing: 80% coverage, Given/When/Then"),
    _file(f"{p}/.kiro/steering/05-responsible-ai-use.md", "Uso responsable IA: plan obligatorio, adherencia arquitectura"),
    _file(f"{p}/.kiro/steering/06-data-access.md", "Acceso datos: ORM obligatorio, no raw SQL"),
    _file(f"{p}/.kiro/steering/07-error-handling.md", "Excepciones: cero 500, captura obligatoria"),
    _file(f"{p}/.kiro/steering/08-observability.md", "Observabilidad: logs por ambiente, masking, correlation-id"),
    _file(f"{p}/.kiro/steering/10-stack-java.md", "Stack Java: JDK 21, Spring Boot 4, Gradle 9"),
    _file(f"{p}/.kiro/hooks/pre-write-gate.json", "Gate pre-escritura: plan + arquitectura + calidad"),
    _file(f"{p}/.kiro/hooks/responsible-use.json", "Validacion prompt: accion + objeto"),
    _file(f"{p}/.kiro/hooks/code-review-gate.json", "Review post-escritura: naming, tests, consistencia"),
    _file(f"{p}/.kiro/hooks/test-coverage-gate.json", "Verificacion tests al completar tarea"),
    _file(f"{p}/.kiro/hooks/build-validate.json", "Compilar al guardar .java"),
    _file(f"{p}/.kiro/hooks/integrity-check.json", "Verificar hooks activos al iniciar sesion"),
    _file(f"{p}/.kiro/hooks/summary-on-completion.json", "Resumen de cambios al finalizar sesion"),
    _file(f"{p}/.kiro/changelogs/changelog-develop.md", "Changelog inicial"),
])
```

**Criterio de done:** `handle_get_project_plan(valid_config)` muestra 18 entradas de `.kiro/` en el tree (antes eran 2).

---

### TASK 17 — Verificar que el proyecto compila y templates renderizan

**Qué hacer:** Ejecutar el MCP localmente y validar que no hay errores.

**Pasos:**

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Verificar imports y sintaxis:
   ```bash
   python -c "from src.models.project_config import ProjectConfig; print('OK')"
   python -c "from src.generators.java_spring_boot import JavaSpringBootGenerator; print('OK')"
   python -c "from src.tools.get_required_inputs import handle_get_required_inputs; print(len(handle_get_required_inputs('java-spring-boot')['categories']), 'categorias')"
   ```

3. Verificar renderizado de templates (crear un test rápido):
   ```python
   from src.utils.template_renderer import TemplateRenderer
   renderer = TemplateRenderer("java-spring-boot")
   
   # Verificar que los templates nuevos existen
   assert renderer.has_template("kiro/project.json.j2")
   assert renderer.has_template("kiro/steering/00-org-conventions.md.j2")
   assert renderer.has_template("kiro/steering/05-responsible-ai-use.md.j2")
   assert renderer.has_template("kiro/hooks/pre-write-gate.json.j2")
   print("Todos los templates existen")
   ```

4. Generar un proyecto de prueba:
   ```python
   import json
   from src.tools.initialize_project import handle_initialize_project
   
   config = {
       "project_name": "test-verificacion-ms",
       "context_path": "/test_verificacion",
       "api_description": "Test de verificacion",
       "api_version": "1.0.0",
       "database": {
           "db_name": "test_db",
           "db_user": "test_user",
           "db_password": "test_pass"
       },
       "modules": [{
           "module_name": "polizas",
           "entity_name": "Poliza",
           "table_name": "POLIZA",
           "fields": [
               {"name": "nombre", "field_type": "String", "column_name": "nombre", "nullable": False, "length": 255}
           ]
       }],
       "i18n": ["es", "en"],
       "cache": "redis",
       "docker_profile": "java-redis"
   }
   
   result = handle_initialize_project(config, "/tmp/test-mcp")
   assert result["status"] == "success", f"Error: {result}"
   print(f"Proyecto generado: {result['files_created']} archivos")
   ```

5. Verificar que los archivos .kiro/ existen en el output:
   ```bash
   ls /tmp/test-mcp/test-verificacion-ms/.kiro/
   ls /tmp/test-mcp/test-verificacion-ms/.kiro/steering/
   ls /tmp/test-mcp/test-verificacion-ms/.kiro/hooks/
   ```

**Criterio de done:**
- 0 errores de import
- Todos los templates existen y renderizan sin error
- Proyecto de prueba genera con status "success"
- Carpeta `.kiro/` contiene: project.json + 10 steering files + 7 hooks + 1 changelog

---

## NOTAS FINALES PARA EL AGENTE EJECUTOR

1. **Orden importa:** Tasks 1-2 son prerequisitos. Tasks 3-13 son independientes entre sí. Task 14 depende de que todos los templates existan. Tasks 15-16 son independientes. Task 17 es validación final.

2. **No inventar contenido:** El contenido de los steering files está 100% definido en `CONSOLIDADO_DISENO_MCP.md`. No agregar reglas, no quitar reglas, no reinterpretar. Copiar textualmente y solo agregar el front-matter de Kiro y las variables Jinja2 donde aplique.

3. **No tocar lo que no se pide:** No modificar templates de `src/`, `infra/`, `gradle/`, `test/`, etc. Solo la carpeta `kiro/` y los archivos de Python indicados.

4. **El template `kiro/api-context.md.j2` se elimina** — su funcionalidad queda absorbida por los nuevos steering files. NO borrarlo del filesystem hasta que Task 14 esté completa (para no romper la compilación intermedia). Borrarlo al final de Task 14.

5. **Si un template steering es muy largo** (más de 200 líneas), está bien. Los steering files son documentos completos de referencia, no snippets.
