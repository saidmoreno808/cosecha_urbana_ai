"""Estado compartido del grafo LangGraph."""
from typing import Annotated, Optional, Any

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Estado del agente LangGraph - se pasa entre nodos."""

    # Input
    alert_id: str
    alert: Optional[Any]  # FoodAlert - Any para evitar importación circular

    # Análisis
    urgency_score: float          # 0.0 - 1.0
    priority_rank: int
    analysis_reasoning: str

    # Matching
    candidate_recipients: list    # list[Recipient]
    selected_recipient: Optional[Any]  # Recipient
    match_score: float
    match_reasoning: str
    distance_km: float

    # Ejecución
    route: Optional[Any]          # Route
    notifications_sent: list[str]
    execution_status: str         # pending | in_progress | completed | failed

    # Validación
    validation_passed: bool
    validation_notes: str

    # Metadata
    steps_taken: list[str]
    errors: list[str]
    started_at: str
    completed_at: Optional[str]

    # Mensajes LangGraph
    messages: Annotated[list, "messages"]
