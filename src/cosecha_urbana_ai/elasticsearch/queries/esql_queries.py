"""ES|QL queries para análisis analítico del agente."""


def get_active_alerts_stats_query(index: str = "cosecha_urbana_food_alerts") -> str:
    """Estadísticas de alertas activas por categoría."""
    return f"""
FROM {index}
| WHERE is_active == true
| STATS
    count = COUNT(*),
    total_kg = SUM(quantity_kg),
    avg_urgency = AVG(urgency_score)
  BY food_category
| SORT avg_urgency DESC
"""


def get_donor_concurrent_alerts_query(
    donor_id: str,
    index: str = "cosecha_urbana_food_alerts",
) -> str:
    """Cuántas alertas activas tiene el mismo donante."""
    return f"""
FROM {index}
| WHERE is_active == true AND donor_id == "{donor_id}"
| STATS count = COUNT(*), avg_kg = AVG(quantity_kg)
| LIMIT 1
"""


def get_priority_rank_query(
    urgency_score: float,
    index: str = "cosecha_urbana_food_alerts",
) -> str:
    """Cuantas alertas tienen mayor urgencia que la actual."""
    return f"""
FROM {index}
| WHERE is_active == true AND urgency_score > {urgency_score}
| STATS count = COUNT(*)
| LIMIT 1
"""


def get_weekly_donations_summary_query(
    index: str = "cosecha_urbana_donations_history",
) -> str:
    """Resumen de donaciones de la última semana."""
    return f"""
FROM {index}
| WHERE @timestamp >= NOW() - 7 days
| STATS
    total_donations = COUNT(*),
    total_kg = SUM(quantity_kg),
    avg_distance_km = AVG(distance_km),
    total_beneficiaries = SUM(beneficiaries_served)
  BY food_category
| SORT total_kg DESC
"""


def get_top_donors_query(
    limit: int = 10,
    index: str = "cosecha_urbana_donations_history",
) -> str:
    """Top donantes por kg donado."""
    return f"""
FROM {index}
| STATS
    total_kg = SUM(quantity_kg),
    total_donations = COUNT(*)
  BY donor_name
| SORT total_kg DESC
| LIMIT {limit}
"""


def get_top_recipients_query(
    limit: int = 10,
    index: str = "cosecha_urbana_donations_history",
) -> str:
    """Top receptores por kg recibido."""
    return f"""
FROM {index}
| STATS
    total_kg = SUM(quantity_kg),
    total_donations = COUNT(*),
    avg_match_score = AVG(match_score)
  BY recipient_name
| SORT total_kg DESC
| LIMIT {limit}
"""


def get_impact_metrics_query(
    index: str = "cosecha_urbana_donations_history",
) -> str:
    """Métricas globales de impacto."""
    return f"""
FROM {index}
| WHERE status == "completed"
| STATS
    total_kg_rescued = SUM(quantity_kg),
    total_donations = COUNT(*),
    total_beneficiaries = SUM(beneficiaries_served),
    avg_coordination_time = AVG(coordination_time_minutes),
    avg_distance = AVG(distance_km)
"""
