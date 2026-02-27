"""Métricas de impacto del sistema."""
import structlog
from ..elasticsearch.client import get_es_client

logger = structlog.get_logger()


async def get_impact_metrics() -> dict:
    """Calcula métricas de impacto usando ES|QL."""
    es = get_es_client()

    query = """
FROM cosecha_urbana_donations_history
| WHERE status == "completed"
| STATS
    total_kg_rescued = SUM(quantity_kg),
    total_donations = COUNT(*),
    total_beneficiaries = SUM(beneficiaries_served),
    avg_coordination_time = AVG(coordination_time_minutes),
    avg_distance_km = AVG(distance_km)
"""

    try:
        result = await es.esql.query(body={"query": query})
        columns = [c["name"] for c in result.get("columns", [])]
        rows = result.get("rows", [])
        if rows:
            metrics = dict(zip(columns, rows[0]))
            # Calcular CO2 evitado aproximado (0.5 kg CO2 por kg de comida)
            kg = metrics.get("total_kg_rescued") or 0
            metrics["co2_saved_kg"] = round(float(kg) * 0.5, 2)
            metrics["meals_equivalent"] = int(float(kg) / 0.35)
            return metrics
        return {"message": "No completed donations yet"}
    except Exception as exc:
        logger.error("Metrics query failed", error=str(exc))
        return {"error": str(exc)}
