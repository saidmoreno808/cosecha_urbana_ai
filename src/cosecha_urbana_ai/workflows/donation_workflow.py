"""Workflow de coordinación de donaciones."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

import structlog

from ..elasticsearch.client import get_es_client
from ..elasticsearch.repositories.donation_repo import DonationRepository
from ..elasticsearch.repositories.alert_repo import AlertRepository
from ..models.donation import Donation
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient

logger = structlog.get_logger()


@dataclass
class WorkflowResult:
    success: bool
    donation_id: str | None = None
    notifications_sent: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class DonationCoordinationWorkflow:
    """
    Coordina la donación de inicio a fin:
    1. Crear registro de donación
    2. Desactivar la alerta
    3. Notificar donante y receptor
    4. Calcular tiempo de coordinación
    """

    def __init__(self) -> None:
        self.es = get_es_client()

    async def execute(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        match_score: float,
        distance_km: float,
        agent_reasoning: str,
        started_at: str,
    ) -> WorkflowResult:
        notifications_sent: list[str] = []
        errors: list[str] = []
        donation_id: str | None = None

        try:
            now = datetime.now(timezone.utc)

            # Calcular tiempo de coordinación
            try:
                start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                coordination_minutes = (now - start_dt).total_seconds() / 60
            except Exception:
                coordination_minutes = 0.0

            # 1. Crear donación
            donation = Donation(
                alert_id=alert.id,
                donor_id=alert.donor_id,
                donor_name=alert.donor_name,
                recipient_id=recipient.id,
                recipient_name=recipient.name,
                food_category=alert.food_category,
                quantity_kg=alert.quantity_kg,
                distance_km=distance_km,
                urgency_level=alert.urgency_level,
                status="in_progress",
                coordination_time_minutes=round(coordination_minutes, 2),
                pickup_location=alert.location,
                delivery_location=recipient.location,
                beneficiaries_served=recipient.beneficiaries_count,
                agent_reasoning=agent_reasoning,
                match_score=match_score,
                created_at=now.isoformat(),
            )

            donation_repo = DonationRepository(self.es)
            alert_repo = AlertRepository(self.es)

            created = await donation_repo.create(donation)
            donation_id = created.id

            # 2. Desactivar alerta
            await alert_repo.deactivate(alert.id, recipient.id)

            # 3. Notificaciones
            logger.info(
                "Notifying donor",
                donor=alert.donor_name,
                donation_id=donation_id,
                recipient=recipient.name,
            )
            notifications_sent.append(f"donor:{alert.donor_id}")

            logger.info(
                "Notifying recipient",
                recipient=recipient.name,
                donation_id=donation_id,
                food=alert.food_category.value,
                kg=alert.quantity_kg,
            )
            notifications_sent.append(f"recipient:{recipient.id}")

            return WorkflowResult(
                success=True,
                donation_id=donation_id,
                notifications_sent=notifications_sent,
                errors=errors,
            )

        except Exception as exc:
            logger.error("Donation workflow failed", error=str(exc))
            errors.append(str(exc))
            return WorkflowResult(
                success=False,
                donation_id=donation_id,
                notifications_sent=notifications_sent,
                errors=errors,
            )
