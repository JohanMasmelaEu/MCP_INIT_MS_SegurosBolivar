# Changelog — main

## [No publicado]

### Agregado
- Se agregó tool `set_output_directory` para configurar una única vez el directorio de salida de proyectos generados
- Se agregó sistema de ingestion de lineamientos de stacks vía PDF/documentos:
  - Tool `ingest_stack_guidelines`: persiste el contenido crudo de un documento en `/settings/guidelines/<stack>/`
  - Tool `get_stack_guidelines`: recupera lineamientos (versión raw o applied) para análisis por el LLM de Kiro
  - Tool `apply_stack_guidelines`: persiste lineamientos refinados y aprobados por el usuario como documentación oficial
- Se agregó endpoint `/api/guidelines/status` en el visualizador para consultar estado de lineamientos por stack
- Se actualizó Admin UI (`/admin`) para mostrar estado de lineamientos ingresados (pendientes/aplicados, categorías, reglas)
- Se actualizó tab "Estándares" del Archetype Visualizer para priorizar guidelines aplicados sobre los hardcoded
- Se agregó módulo `src/utils/settings.py` para persistir configuración del MCP entre sesiones en volumen Docker `/settings`
- Se agregó volumen `/settings` en Dockerfile para persistencia de configuración
- Se agregó Archetype Visualizer UI en puerto 9752 (`src/engine/visualizer.py` + `visualizer_ui.html`)
  - Tab Arquetipo: árbol de directorios interactivo del proyecto generado
  - Tab Estándares: tabla de reglas por categoría (naming, arquitectura, testing, seguridad, libs, CI/CD, observabilidad)
  - Tab Decisiones: cards con las configuraciones elegidas (auth, DB, integraciones, módulos)
  - Tab Blueprint: texto completo del blueprint técnico del stack
- Se agregó Admin UI en `/admin` (`src/engine/admin_ui.html`) con formulario para registrar nuevos stacks tecnológicos
  - Crea estructura de directorios en `templates/<stack>/`
  - Genera blueprint placeholder en `blueprints/`
  - Genera generator placeholder en `src/generators/`
  - Muestra stacks existentes con conteo de templates
- Se agregó MCP Marketplace en `get_required_inputs` — catálogo de MCP Servers disponibles con descripciones y capabilities
  - MCP_INIT_MS_SegurosBolivar (auto-incluido): extensión de proyectos desde Kiro
  - MCP_HU_SegurosBolivar (opcional): análisis de historias de usuario con panel de expertos
- Se agregó modelo `McpServerSelection` en `project_config.py` y campo `selected_mcps` en `ProjectConfig`
- Se agregaron 4 hooks por stack Java Spring Boot generados automáticamente en proyectos:
  - `compile-on-save.json`: compila al guardar archivos .java
  - `test-after-task.json`: ejecuta tests al completar una tarea de spec
  - `code-standards-check.json`: verifica estándares de código antes de escribir archivos
  - `security-review.json`: revisa archivos de seguridad/configuración al guardarlos
- Se agregó template `.kiro/settings/mcp.json.j2` que genera config de MCP servers según selección del marketplace
- Se agregó template `.kiro/specs/project-initialization.md.j2` que genera spec inicial con requirements, design y tasks del proyecto

### Cambiado
- Se modificó `initialize_project` para usar el directorio configurado como default cuando no se pasa `target_path`
- Se reemplazó volumen `/workspace` por `/repos` (bind mount) + `/settings` (volumen nombrado) en Dockerfile
- Se actualizó `server.py` para registrar tool `set_output_directory`, hacer `target_path` opcional, y arrancar visualizador en boot
- Se actualizó `java_spring_boot.py` generator: ahora genera hooks, mcp.json y specs en `_generate_kiro_context()`
- Se actualizó `initialize_project.py` para notificar al visualizador tras generar un proyecto
- Se actualizó README con configuración Docker correcta, diagrama de arquitectura y documentación completa
- Se eliminó variable de entorno `MCP_WORKSPACE_PATH` del Dockerfile (ya no es necesaria)
- Se expone puerto 9752 en Dockerfile para el Archetype Visualizer
