"""
Nodo 2: ANALYZE
Usa ES|QL para calcular urgencia, prioridad y patrones de la alerta.
"""
import structlog

from ...elasticsearch.client import get_es_client
from ...elasticsearch.queries.esql_queries import (
    get_donor_concurrent_alerts_query,
    get_priority_rank_query,
)
from ...models.agent_state import AgentState
from ...models.food_alert import FoodCategory

logger = structlog.get_logger()

# Pesos de urgencia por categoría
CATEGORY_WEIGHTS: dict[str, float] = {
    FoodCategory.PREPARED.value: 1.0,
    FoodCategory.MEAT.value: 0.9,
    FoodCategory.DAIRY.value: 0.85,
    FoodCategory.BAKERY.value: 0.8,
    FoodCategory.PRODUCE.value: 0.7,
    FoodCategory.DRY_GOODS.value: 0.3,
}


async def run(state: AgentState) -> AgentState:
    """Calcula urgency_score y priority_rank usando ES|QL."""
    alert = state["alert"]
    steps = list(state.get("steps_taken", []))
    errors = list(state.get("errors", []))
    steps.append("analyze_node:started")

    logger.info("Analyzing alert", alert_id=alert.id, category=alert.food_category)

    es = get_es_client()

    # -- 1. Score base: tiempo restante x factor de categoría -------------
    hours_left = alert.hours_until_expiry
    time_urgency = max(0.0, min(1.0, 1.0 - (hours_left / 24.0)))
    category_factor = CATEGORY_WEIGHTS.get(alert.food_category.value, 0.5)
    urgency_score = time_urgency * category_factor

    # -- 2. ES|QL: alertas concurrentes del mismo donante -----------------
    concurrent_alerts = 0
    try:
        query = get_donor_concurrent_alerts_query(alert.donor_id)
        result = await es.esql.query(body={"query": query})
        rows = result.get("rows", [])
        if rows:
            concurrent_alerts = int(rows[0][0])
            # Boost si el donante tiene muchas alertas activas
            if concurrent_alerts > 3:
                urgency_score = min(1.0, urgency_score * 1.15)
    except Exception as exc:
        logger.warning("ES|QL concurrent alerts query failed", error=str(exc))

    # -- 3. ES|QL: ranking de prioridad relativa ---------------------------
    priority_rank = 1
    try:
        rank_query = get_priority_rank_query(urgency_score)
        rank_result = await es.esql.query(body={"query": rank_query})
        rows = rank_result.get("rows", [])
        if rows:
            priority_rank = int(rows[0][0]) + 1
    except Exception as exc:
        logger.warning("ES|QL priority rank query failed", error=str(exc))

    reasoning = (
        f"Alerta analizada: {hours_left:.1f}h hasta vencimiento. "
        f"Categoría '{alert.food_category.value}' (factor={category_factor:.2f}). "
        f"Urgency score: {urgency_score:.3f}/1.0. "
        f"Alertas concurrentes del donante: {concurrent_alerts}. "
        f"Prioridad relativa: #{priority_rank} entre alertas activas."
    )

    steps.append("analyze_node:completed")
    logger.info(
        "Analysis complete",
        urgency_score=urgency_score,
        priority_rank=priority_rank,
        hours_left=hours_left,
    )

    return {
        **state,
        "urgency_score": round(urgency_score, 4),
        "priority_rank": priority_rank,
        "analysis_reasoning": reasoning,
        "steps_taken": steps,
        "errors": errors,
    }
