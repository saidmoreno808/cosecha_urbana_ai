"""
Nodo 1: INGEST
Recupera y valida la alerta de excedente desde Elasticsearch.
"""
from datetime import datetime, timezone

import structlog

from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.alert_repo import AlertRepository
from ...models.agent_state import AgentState

logger = structlog.get_logger()


async def run(state: AgentState) -> AgentState:
    """Recupera la alerta por ID y valida que esté activa."""
    alert_id = state["alert_id"]
    steps = list(state.get("steps_taken", []))
    errors = list(state.get("errors", []))
    steps.append("ingest_node:started")

    logger.info("Ingesting alert", alert_id=alert_id)

    try:
        es = get_es_client()
        repo = AlertRepository(es)
        alert = await repo.get_by_id(alert_id)

        if not alert:
            errors.append(f"Alert {alert_id} not found in Elasticsearch")
            return {
                **state,
                "alert": None,
                "steps_taken": steps,
                "errors": errors,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        if not alert.is_active:
            errors.append(f"Alert {alert_id} is no longer active (already matched)")
            return {
                **state,
                "alert": None,
                "steps_taken": steps,
                "errors": errors,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        if alert.hours_until_expiry <= 0:
            errors.append(f"Alert {alert_id} has already expired")
            return {
                **state,
                "alert": None,
                "steps_taken": steps,
                "errors": errors,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        # Recalcular urgencia fresca
        alert.urgency_level = alert.compute_urgency()

        steps.append("ingest_node:completed")
        logger.info(
            "Alert ingested successfully",
            alert_id=alert_id,
            donor=alert.donor_name,
            category=alert.food_category,
            hours_left=f"{alert.hours_until_expiry:.1f}",
            urgency=alert.urgency_level,
        )

        return {
            **state,
            "alert": alert,
            "steps_taken": steps,
            "errors": errors,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Ingest node error", error=str(exc), alert_id=alert_id)
        errors.append(f"Ingest error: {exc}")
        steps.append("ingest_node:failed")
        return {
            **state,
            "alert": None,
            "steps_taken": steps,
            "errors": errors,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
