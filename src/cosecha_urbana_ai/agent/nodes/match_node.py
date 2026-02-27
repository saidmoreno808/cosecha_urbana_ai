"""
Nodo 3: MATCH
Encuentra el receptor optimo usando Geo Search + LLM reasoning.
Soporta Groq (llama-3.3-70b-versatile) como proveedor principal
y Anthropic Claude como fallback opcional.
"""
import json

import structlog

from ...config import get_settings
from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.recipient_repo import RecipientRepository
from ...models.agent_state import AgentState

logger = structlog.get_logger()


def _build_llm(settings):
    """Crea el cliente LLM segun la configuracion activa."""
    if settings.use_groq:
        from langchain_groq import ChatGroq  # noqa: PLC0415

        logger.info("Using Groq LLM", model=settings.groq_model)
        return ChatGroq(
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
            api_key=settings.groq_api_key,
        )

    # Fallback: Anthropic
    from langchain_anthropic import ChatAnthropic  # noqa: PLC0415

    logger.info("Using Anthropic LLM", model=settings.llm_model)
    return ChatAnthropic(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.anthropic_api_key,
    )


async def run(state: AgentState) -> AgentState:
    """
    Matching en 3 capas:
    1. GEO + COMPATIBILITY filter (Elasticsearch)
    2. Multi-criteria scoring (distancia, necesidad, historial, beneficiarios)
    3. LLM reasoning (Claude valida y explica el match final)
    """
    alert = state["alert"]
    settings = get_settings()
    steps = list(state.get("steps_taken", []))
    errors = list(state.get("errors", []))
    steps.append("match_node:started")

    logger.info("Finding recipient match", alert_id=alert.id)

    es = get_es_client()
    repo = RecipientRepository(es)

    # -- CAPA 1: Geo + compatibilidad --------------------------------------
    requires_refrigeration = "refrigeration" in (alert.special_requirements or [])
    geo_compatible = await repo.find_compatible_recipients(
        lat=alert.location.lat,
        lon=alert.location.lon,
        max_km=settings.max_distance_km,
        food_category=alert.food_category,
        quantity_kg=alert.quantity_kg,
        requires_refrigeration=requires_refrigeration,
    )

    if not geo_compatible:
        logger.warning(
            "No compatible recipients found",
            alert_id=alert.id,
            radius_km=settings.max_distance_km,
        )
        steps.append("match_node:no_recipients")
        return {
            **state,
            "candidate_recipients": [],
            "selected_recipient": None,
            "match_score": 0.0,
            "match_reasoning": (
                f"No se encontraron receptores compatibles en radio de "
                f"{settings.max_distance_km}km para categoría '{alert.food_category.value}'."
            ),
            "distance_km": 0.0,
            "steps_taken": steps,
            "errors": errors,
        }

    # -- CAPA 2: Scoring multi-criterio ------------------------------------
    need_score_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}

    scored: list[tuple[float, object]] = []
    for r in geo_compatible:
        dist_km = r.distance_km or settings.max_distance_km
        dist_score = max(0.0, 1.0 - (dist_km / settings.max_distance_km))
        need_score = need_score_map.get(r.current_need_level, 0.5)
        history_score = max(0.0, 1.0 - (r.total_donations_received / 100))
        beneficiary_score = min(1.0, r.beneficiaries_count / 200)

        composite = (
            dist_score * 0.30
            + need_score * 0.35
            + history_score * 0.15
            + beneficiary_score * 0.20
        )
        scored.append((composite, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    top3 = scored[:3]

    # -- CAPA 3: LLM Reasoning (Claude) -----------------------------------
    candidates_summary = []
    for score, r in top3:
        candidates_summary.append(
            {
                "id": r.id,
                "name": r.name,
                "type": r.organization_type,
                "distance_km": round(r.distance_km or 0, 2),
                "beneficiaries": r.beneficiaries_count,
                "need_level": r.current_need_level,
                "composite_score": round(score, 3),
                "accepted_categories": [c.value if hasattr(c, "value") else c
                                         for c in r.accepted_food_categories],
            }
        )

    try:
        llm = _build_llm(settings)

        prompt = f"""Eres el sistema de matching de cosecha_urbana_ai.

ALERTA DE EXCEDENTE:
- Alimento: {alert.food_category.value} - {alert.description}
- Cantidad: {alert.quantity_kg} kg
- Horas hasta vencimiento: {alert.hours_until_expiry:.1f}h
- Urgencia score: {state.get("urgency_score", 0):.2f}/1.0
- Requerimientos especiales: {alert.special_requirements or []}

CANDIDATOS RECEPTORES (top {len(top3)}):
{json.dumps(candidates_summary, ensure_ascii=False, indent=2)}

Selecciona el MEJOR receptor considerando:
1. Urgencia de la donación vs capacidad del receptor
2. Distancia para maximizar viabilidad logística
3. Impacto (beneficiarios atendidos)
4. Necesidad actual del receptor

Responde ÚNICAMENTE en JSON con este formato exacto:
{{
  "selected_id": "id_del_receptor",
  "confidence": 0.85,
  "reasoning": "Explicación en español de 2-3 oraciones"
}}"""

        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        # Extraer JSON aunque venga con texto extra
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        llm_result = json.loads(content)
        selected_id = llm_result["selected_id"]
        match_score = float(llm_result["confidence"])
        reasoning = llm_result["reasoning"]

    except Exception as exc:
        logger.warning("LLM match reasoning failed, using top score", error=str(exc))
        selected_id = top3[0][1].id
        match_score = float(top3[0][0])
        reasoning = f"Match automático por score compuesto: {match_score:.2f}"

    # Recuperar el recipient seleccionado
    selected = next(
        (r for _, r in top3 if r.id == selected_id),
        top3[0][1],
    )

    steps.append("match_node:completed")
    logger.info(
        "Match found",
        recipient=selected.name,
        score=match_score,
        distance_km=selected.distance_km,
    )

    return {
        **state,
        "candidate_recipients": [r for _, r in top3],
        "selected_recipient": selected,
        "match_score": round(match_score, 4),
        "match_reasoning": reasoning,
        "distance_km": round(selected.distance_km or 0.0, 2),
        "steps_taken": steps,
        "errors": errors,
    }
