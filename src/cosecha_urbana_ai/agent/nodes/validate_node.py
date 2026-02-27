"""
Nodo 5: VALIDATE
Valida el resultado final del agente y actualiza el estado.
"""
from datetime import datetime, timezone

import structlog

from ...models.agent_state import AgentState

logger = structlog.get_logger()


async def run(state: AgentState) -> AgentState:
    """Valida el resultado y cierra el ciclo del agente."""
    steps = list(state.get("steps_taken", []))
    errors = list(state.get("errors", []))
    steps.append("validate_node:started")

    completed_at = datetime.now(timezone.utc).isoformat()
    validation_notes = []
    validation_passed = False

    execution_status = state.get("execution_status", "")
    selected_recipient = state.get("selected_recipient")
    match_score = state.get("match_score", 0.0)

    # -- Validaciones ------------------------------------------------------
    if not selected_recipient:
        validation_notes.append("FAIL: No se encontró receptor compatible")
        validation_passed = False
    elif execution_status == "failed":
        validation_notes.append("FAIL: La ejecución de la donación falló")
        validation_passed = False
    elif execution_status == "completed":
        validation_notes.append("OK: Donación coordinada exitosamente")
        if match_score >= 0.7:
            validation_notes.append(f"OK: Match score alto ({match_score:.2f})")
        elif match_score >= 0.4:
            validation_notes.append(f"WARN: Match score moderado ({match_score:.2f})")
        else:
            validation_notes.append(f"WARN: Match score bajo ({match_score:.2f})")

        notifications = state.get("notifications_sent", [])
        if notifications:
            validation_notes.append(f"OK: {len(notifications)} notificaciones enviadas")

        validation_passed = True
    elif not execution_status:
        # Llegó al validate sin pasar por execute (no_recipient o low_match)
        validation_notes.append("INFO: Proceso terminado sin match suficiente")
        validation_passed = False

    # -- Errores acumulados ------------------------------------------------
    if errors:
        validation_notes.append(f"ERRORS: {len(errors)} error(s) durante el proceso")
        validation_passed = False

    notes_str = " | ".join(validation_notes)
    steps.append("validate_node:completed")

    logger.info(
        "Validation complete",
        passed=validation_passed,
        notes=notes_str,
        alert_id=state.get("alert_id"),
    )

    return {
        **state,
        "validation_passed": validation_passed,
        "validation_notes": notes_str,
        "completed_at": completed_at,
        "steps_taken": steps,
        "errors": errors,
    }
