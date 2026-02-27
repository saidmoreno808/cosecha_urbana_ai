"""Router del agente IA - endpoint principal del hackathon."""
import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...agent.graph import create_agent_graph
from ...models.agent_state import AgentState

logger = structlog.get_logger()
router = APIRouter()


class AgentTriggerRequest(BaseModel):
    alert_id: str
    force: bool = False


class AgentResponse(BaseModel):
    success: bool
    alert_id: str
    selected_recipient_id: str | None = None
    selected_recipient_name: str | None = None
    distance_km: float | None = None
    urgency_score: float | None = None
    match_score: float | None = None
    coordination_time_seconds: float
    steps_taken: list[str]
    reasoning: str
    errors: list[str]
    validation_notes: str = ""


@router.post("/trigger", response_model=AgentResponse)
async def trigger_agent(request: AgentTriggerRequest):
    """
    Dispara el agente multi-paso para coordinar una donación.

    Flujo:
    1. INGEST  - Recupera y valida la alerta
    2. ANALYZE - ES|QL calcula urgencia y prioridad
    3. MATCH   - Geo + LLM encuentra receptor óptimo
    4. EXECUTE - Registra donación y notifica
    5. VALIDATE - Cierra el ciclo y verifica resultado
    """
    logger.info("Agent trigger received", alert_id=request.alert_id)
    start = time.time()

    initial_state: AgentState = {
        "alert_id": request.alert_id,
        "alert": None,
        "urgency_score": 0.0,
        "priority_rank": 0,
        "analysis_reasoning": "",
        "candidate_recipients": [],
        "selected_recipient": None,
        "match_score": 0.0,
        "match_reasoning": "",
        "distance_km": 0.0,
        "route": None,
        "notifications_sent": [],
        "execution_status": "pending",
        "validation_passed": False,
        "validation_notes": "",
        "steps_taken": [],
        "errors": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "messages": [],
    }

    try:
        graph = create_agent_graph()
        final_state = await graph.ainvoke(initial_state)
        elapsed = time.time() - start

        recipient = final_state.get("selected_recipient")

        logger.info(
            "Agent completed",
            alert_id=request.alert_id,
            success=final_state.get("validation_passed"),
            elapsed=f"{elapsed:.2f}s",
            steps=len(final_state.get("steps_taken", [])),
        )

        return AgentResponse(
            success=final_state.get("validation_passed", False),
            alert_id=request.alert_id,
            selected_recipient_id=recipient.id if recipient else None,
            selected_recipient_name=recipient.name if recipient else None,
            distance_km=final_state.get("distance_km"),
            urgency_score=final_state.get("urgency_score"),
            match_score=final_state.get("match_score"),
            coordination_time_seconds=round(elapsed, 2),
            steps_taken=final_state.get("steps_taken", []),
            reasoning=final_state.get("match_reasoning", ""),
            errors=final_state.get("errors", []),
            validation_notes=final_state.get("validation_notes", ""),
        )

    except Exception as exc:
        elapsed = time.time() - start
        logger.error("Agent execution failed", error=str(exc), alert_id=request.alert_id)
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(exc)}",
        )


@router.get("/status")
async def agent_status():
    """Estado del agente y estadísticas de ejecución."""
    return {
        "agent": "cosecha_urbana_ai",
        "version": "0.1.0",
        "model": "LangGraph + Claude",
        "steps": ["ingest", "analyze", "match", "execute", "validate"],
        "status": "ready",
    }
