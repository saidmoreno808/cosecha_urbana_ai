"""
Grafo LangGraph del agente cosecha_urbana_ai.

Flujo de 5 pasos:
  INGEST -> ANALYZE -> MATCH -> EXECUTE -> VALIDATE
"""
import structlog
from langgraph.graph import END, StateGraph

from ..models.agent_state import AgentState
from .nodes import analyze_node, execute_node, ingest_node, match_node, validate_node

logger = structlog.get_logger()


# -- Routers condicionales -----------------------------------------------------

def route_after_ingest(state: AgentState) -> str:
    """¿La alerta existe y es válida?"""
    if state.get("errors"):
        logger.warning("Ingest failed, ending", errors=state["errors"])
        return "failed"
    if not state.get("alert"):
        return "failed"
    return "analyze"


def route_after_analyze(state: AgentState) -> str:
    """¿El análisis tuvo errores?"""
    if state.get("errors"):
        return "failed"
    urgency = state.get("urgency_score", 0)
    if urgency >= 0.9:
        logger.warning("CRITICAL urgency alert", score=urgency, alert_id=state.get("alert_id"))
    return "match"


def route_after_match(state: AgentState) -> str:
    """¿Se encontró un receptor compatible?"""
    if not state.get("selected_recipient"):
        logger.warning("No recipient found", alert_id=state.get("alert_id"))
        return "no_recipient"
    if state.get("match_score", 0) < 0.2:
        logger.warning("Match score too low", score=state.get("match_score"))
        return "low_match"
    return "execute"


# -- Factory del grafo ---------------------------------------------------------

def create_agent_graph():
    """Compila y devuelve el StateGraph del agente."""
    workflow = StateGraph(AgentState)

    # Registrar nodos
    workflow.add_node("ingest", ingest_node.run)
    workflow.add_node("analyze", analyze_node.run)
    workflow.add_node("match", match_node.run)
    workflow.add_node("execute", execute_node.run)
    workflow.add_node("validate", validate_node.run)

    # Entry point
    workflow.set_entry_point("ingest")

    # Transiciones
    workflow.add_conditional_edges(
        "ingest",
        route_after_ingest,
        {"analyze": "analyze", "failed": END},
    )

    workflow.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {"match": "match", "failed": END},
    )

    workflow.add_conditional_edges(
        "match",
        route_after_match,
        {
            "execute": "execute",
            "no_recipient": "validate",
            "low_match": "validate",
        },
    )

    workflow.add_edge("execute", "validate")
    workflow.add_edge("validate", END)

    return workflow.compile()
