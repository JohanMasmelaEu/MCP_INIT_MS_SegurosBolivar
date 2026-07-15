"""Tools para ingestion y gestion de lineamientos de stacks tecnologicos.

Flujo de uso:
1. El usuario adjunta un PDF/documento con lineamientos del stack en el chat de Kiro.
2. Kiro extrae el texto del documento (Kiro puede leer PDFs nativamente).
3. Kiro invoca ingest_stack_guidelines(stack_id, raw_content) → MCP persiste el contenido crudo.
4. Kiro (con su LLM) interpreta el contenido y genera un analisis estructurado.
5. Kiro muestra al usuario: "Asi entendi los lineamientos: ..."
6. El usuario refina: "Correcto" o "Ajusta esto..."
7. Kiro invoca apply_stack_guidelines(stack_id, refined_guidelines) → MCP persiste como documentacion oficial.

El MCP NO tiene LLM. Solo almacena y sirve datos. La inferencia la hace Kiro.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mcp_init_ms.tools.stack_guidelines")

GUIDELINES_DIR = Path("/settings/guidelines")
BLUEPRINTS_DIR = Path(__file__).resolve().parent.parent.parent / "blueprints"


def _ensure_guidelines_dir() -> Path:
    """Crea el directorio de guidelines si no existe.

    Returns:
        Path al directorio de guidelines.
    """
    GUIDELINES_DIR.mkdir(parents=True, exist_ok=True)
    return GUIDELINES_DIR


def _get_stack_dir(stack_id: str) -> Path:
    """Obtiene el directorio de guidelines para un stack especifico.

    Args:
        stack_id: Identificador del stack.

    Returns:
        Path al directorio del stack.
    """
    stack_dir = _ensure_guidelines_dir() / stack_id
    stack_dir.mkdir(parents=True, exist_ok=True)
    return stack_dir


def handle_ingest_stack_guidelines(stack_id: str, raw_content: str, source_filename: str = "") -> dict:
    """Persiste el contenido crudo de un documento de lineamientos.

    Guarda el texto extraido del PDF/documento para que Kiro lo procese
    con su LLM y genere un analisis estructurado.

    Args:
        stack_id: Identificador del stack (ej: java-spring-boot).
        raw_content: Texto completo extraido del documento.
        source_filename: Nombre original del archivo fuente (opcional).

    Returns:
        Resultado con status, path guardado y metadata.
    """
    if not stack_id or not stack_id.strip():
        return {"status": "error", "message": "stack_id es requerido."}

    if not raw_content or len(raw_content.strip()) < 50:
        return {
            "status": "error",
            "message": "El contenido es demasiado corto. Asegurate de extraer el texto completo del documento.",
        }

    stack_dir = _get_stack_dir(stack_id)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    # Guardar contenido crudo
    raw_file = stack_dir / f"raw-{timestamp}.txt"
    raw_file.write_text(raw_content, encoding="utf-8")

    # Guardar metadata
    metadata = {
        "stack_id": stack_id,
        "source_filename": source_filename,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "content_length": len(raw_content),
        "status": "pending_analysis",
        "raw_file": raw_file.name,
    }
    metadata_file = stack_dir / "metadata.json"

    # Leer metadata existente o crear nueva
    existing_metadata = {"ingestions": []}
    if metadata_file.exists():
        try:
            existing_metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    existing_metadata["ingestions"].append(metadata)
    existing_metadata["last_ingestion"] = metadata
    metadata_file.write_text(json.dumps(existing_metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Guidelines ingested para stack '%s': %d caracteres", stack_id, len(raw_content))

    return {
        "status": "success",
        "stack_id": stack_id,
        "content_length": len(raw_content),
        "raw_file": str(raw_file),
        "message": (
            f"Contenido de lineamientos guardado ({len(raw_content)} caracteres). "
            "Ahora analiza el contenido con tu LLM y presenta al usuario un resumen "
            "estructurado de los estandares detectados. El usuario refinara si es correcto. "
            "Una vez aprobado, llama apply_stack_guidelines con el resultado estructurado."
        ),
        "next_action": "analyze_with_llm",
        "instructions_for_kiro": (
            "Lee el contenido guardado con get_stack_guidelines y generá un analisis estructurado "
            "con las siguientes categorias: naming, arquitectura, testing, seguridad, librerias aprobadas, "
            "CI/CD, observabilidad, y cualquier otra que detectes en el documento. "
            "Presenta el resultado al usuario para que confirme o ajuste."
        ),
    }


def handle_get_stack_guidelines(stack_id: str, version: str = "latest") -> dict:
    """Obtiene los lineamientos almacenados para un stack.

    Args:
        stack_id: Identificador del stack.
        version: "latest" para el ultimo, "raw" para el crudo, "applied" para el aprobado.

    Returns:
        Contenido de los lineamientos segun la version solicitada.
    """
    stack_dir = _get_stack_dir(stack_id)
    metadata_file = stack_dir / "metadata.json"

    if not metadata_file.exists():
        return {
            "status": "no_guidelines",
            "stack_id": stack_id,
            "message": (
                f"No hay lineamientos ingresados para el stack '{stack_id}'. "
                "El usuario puede adjuntar un PDF con los lineamientos en el chat."
            ),
        }

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

    if version == "applied":
        applied_file = stack_dir / "applied-guidelines.json"
        if not applied_file.exists():
            return {
                "status": "not_applied",
                "stack_id": stack_id,
                "message": "Hay lineamientos ingresados pero no se han aplicado aun.",
                "metadata": metadata.get("last_ingestion"),
            }
        applied = json.loads(applied_file.read_text(encoding="utf-8"))
        return {"status": "ok", "stack_id": stack_id, "version": "applied", "guidelines": applied}

    if version == "raw" or version == "latest":
        last = metadata.get("last_ingestion")
        if not last:
            return {"status": "no_guidelines", "stack_id": stack_id, "message": "Sin ingestions."}

        raw_file = stack_dir / last["raw_file"]
        if not raw_file.exists():
            return {"status": "error", "message": f"Archivo raw no encontrado: {last['raw_file']}"}

        raw_content = raw_file.read_text(encoding="utf-8")

        return {
            "status": "ok",
            "stack_id": stack_id,
            "version": "raw",
            "source_filename": last.get("source_filename", ""),
            "ingested_at": last.get("ingested_at", ""),
            "content_length": len(raw_content),
            "content": raw_content,
            "instructions_for_kiro": (
                "Analiza este contenido y genera un JSON estructurado con los estandares detectados. "
                "Categorias esperadas: naming, architecture, testing, security, approved_libraries, "
                "cicd, observability, performance, error_handling. Cada categoria tiene rules con: "
                "rule (nombre), convention (que hacer), example (codigo o patron). "
                "Muestra el resultado al usuario antes de aplicar."
            ),
        }

    return {"status": "error", "message": f"Version '{version}' no reconocida. Usa: latest, raw, applied."}


def handle_apply_stack_guidelines(
    stack_id: str,
    refined_guidelines: dict,
    update_blueprint: bool = True,
    replace_existing: bool = False,
) -> dict:
    """Persiste los lineamientos refinados como documentacion oficial del stack.

    Despues de que Kiro analizo el documento y el usuario aprobo el resultado,
    esta funcion lo persiste como guidelines aplicados y opcionalmente actualiza
    el blueprint del stack.

    Args:
        stack_id: Identificador del stack.
        refined_guidelines: JSON estructurado con los estandares aprobados por el usuario.
            Formato esperado:
            {
                "stack_name": "Java 21 + Spring Boot 4.x",
                "categories": [
                    {
                        "name": "Naming",
                        "rules": [
                            {"rule": "Clases", "convention": "PascalCase", "example": "PolicyService"}
                        ]
                    }
                ]
            }
        update_blueprint: Si True, actualiza el blueprint del stack en blueprints/.
        replace_existing: Si True, reemplaza los guidelines existentes. Si False, los mergea.

    Returns:
        Resultado con status y paths actualizados.
    """
    if not stack_id or not stack_id.strip():
        return {"status": "error", "message": "stack_id es requerido."}

    if not refined_guidelines:
        return {"status": "error", "message": "refined_guidelines es requerido (JSON con estandares aprobados)."}

    # Validar estructura minima
    if "categories" not in refined_guidelines:
        return {
            "status": "error",
            "message": (
                "refined_guidelines debe tener al menos 'categories' (array de objetos con 'name' y 'rules'). "
                "Formato: {\"stack_name\": \"...\", \"categories\": [{\"name\": \"...\", \"rules\": [...]}]}"
            ),
        }

    stack_dir = _get_stack_dir(stack_id)

    # Guardar guidelines aplicados
    applied_file = stack_dir / "applied-guidelines.json"

    if not replace_existing and applied_file.exists():
        try:
            existing = json.loads(applied_file.read_text(encoding="utf-8"))
            # Merge: agregar categorias nuevas, actualizar existentes
            existing_names = {c["name"] for c in existing.get("categories", [])}
            for cat in refined_guidelines.get("categories", []):
                if cat["name"] in existing_names:
                    # Reemplazar categoria existente
                    existing["categories"] = [
                        cat if c["name"] == cat["name"] else c
                        for c in existing["categories"]
                    ]
                else:
                    existing["categories"].append(cat)
            refined_guidelines = existing
        except (json.JSONDecodeError, OSError):
            pass

    # Agregar metadata de aplicacion
    refined_guidelines["applied_at"] = datetime.now(timezone.utc).isoformat()
    refined_guidelines["stack_id"] = stack_id

    applied_file.write_text(
        json.dumps(refined_guidelines, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Actualizar metadata
    metadata_file = stack_dir / "metadata.json"
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            metadata["last_applied"] = {
                "applied_at": refined_guidelines["applied_at"],
                "categories_count": len(refined_guidelines.get("categories", [])),
                "total_rules": sum(
                    len(c.get("rules", [])) for c in refined_guidelines.get("categories", [])
                ),
            }
            metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            pass

    updated_files = [str(applied_file)]

    # Actualizar blueprint si se solicita
    if update_blueprint:
        blueprint_content = _generate_blueprint_from_guidelines(stack_id, refined_guidelines)
        blueprint_filename = f"{stack_id.upper().replace('-', '_')}_BLUEPRINT.md"
        blueprint_file = BLUEPRINTS_DIR / blueprint_filename

        if replace_existing or not blueprint_file.exists():
            blueprint_file.write_text(blueprint_content, encoding="utf-8")
            updated_files.append(str(blueprint_file))
            logger.info("Blueprint actualizado: %s", blueprint_file)

    logger.info(
        "Guidelines aplicados para stack '%s': %d categorias, %d reglas",
        stack_id,
        len(refined_guidelines.get("categories", [])),
        sum(len(c.get("rules", [])) for c in refined_guidelines.get("categories", [])),
    )

    return {
        "status": "success",
        "stack_id": stack_id,
        "categories_count": len(refined_guidelines.get("categories", [])),
        "total_rules": sum(len(c.get("rules", [])) for c in refined_guidelines.get("categories", [])),
        "updated_files": updated_files,
        "message": (
            f"Lineamientos aplicados exitosamente para '{stack_id}'. "
            f"{len(refined_guidelines.get('categories', []))} categorias con "
            f"{sum(len(c.get('rules', [])) for c in refined_guidelines.get('categories', []))} reglas totales. "
            "El Archetype Visualizer (localhost:9752) ahora mostrara estos estandares en el tab 'Estandares'."
        ),
    }


def _generate_blueprint_from_guidelines(stack_id: str, guidelines: dict) -> str:
    """Genera un blueprint Markdown a partir de guidelines estructurados.

    Args:
        stack_id: Identificador del stack.
        guidelines: JSON con categories y rules.

    Returns:
        Contenido Markdown del blueprint.
    """
    stack_name = guidelines.get("stack_name", stack_id.replace("-", " ").title())
    lines = [
        f"# {stack_name} — Technical Blueprint",
        "",
        f"**Stack:** {stack_id}",
        f"**Generado:** {guidelines.get('applied_at', 'N/A')}",
        "",
        "---",
        "",
    ]

    for category in guidelines.get("categories", []):
        lines.append(f"## {category['name']}")
        lines.append("")

        rules = category.get("rules", [])
        if rules:
            lines.append("| Regla | Convencion | Ejemplo |")
            lines.append("|-------|-----------|---------|")
            for rule in rules:
                r = rule.get("rule", "")
                c = rule.get("convention", "")
                e = rule.get("example", "")
                lines.append(f"| {r} | {c} | `{e}` |")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Blueprint generado automaticamente desde documento de lineamientos aprobado por el equipo.*")

    return "\n".join(lines)
