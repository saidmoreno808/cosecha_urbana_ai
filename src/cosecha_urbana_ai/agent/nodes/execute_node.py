"""
Node 4: EXECUTE
Creates the donation record in Elasticsearch, updates alert status,
and fires real-time notifications via Slack (webhook or Kibana connector).
"""
import time

import structlog

from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.alert_repo import AlertRepository
from ...elasticsearch.repositories.donation_repo import DonationRepository
from ...models.agent_state import AgentState
from ...models.donation import Donation
from ...notifications.dispatcher import NotificationDispatcher

logger = structlog.get_logger()


async def run(state: AgentState) -> AgentState:
    """
    Executes the donation coordination:
      1. Create donation record in Elasticsearch
      2. Deactivate the food alert (is_active = False)
      3. Notify donor via Slack
      4. Notify recipient via Slack
      5. Post ops summary to the monitoring channel
    """
    alert = state["alert"]
    recipient = state["selected_recipient"]
    steps = list(state.get("steps_taken", []))
    errors = list(state.get("errors", []))
    steps.append("execute_node:started")
    t_start = time.time()

    logger.info(
        "Executing donation",
        alert_id=alert.id,
        recipient=recipient.name,
        kg=alert.quantity_kg,
        distance_km=state.get("distance_km"),
    )

    es = get_es_client()
    donation_repo = DonationRepository(es)
    alert_repo = AlertRepository(es)
    notifier = NotificationDispatcher()
    notifications_sent: list[str] = list(state.get("notifications_sent", []))

    try:
        # -- 1. Create donation record -------------------------------------
        donation = Donation(
            alert_id=alert.id,
            donor_id=alert.donor_id,
            donor_name=alert.donor_name,
            recipient_id=recipient.id,
            recipient_name=recipient.name,
            food_category=alert.food_category,
            quantity_kg=alert.quantity_kg,
            distance_km=state.get("distance_km", 0.0),
            urgency_level=alert.urgency_level,
            status="in_progress",
            pickup_location=alert.location,
            delivery_location=recipient.location,
            beneficiaries_served=recipient.beneficiaries_count,
            agent_reasoning=state.get("match_reasoning", ""),
            match_score=state.get("match_score", 0.0),
        )
        created_donation = await donation_repo.create(donation)
        donation_id = created_donation.id
        logger.info("Donation record created", donation_id=donation_id)

        # -- 2. Deactivate the food alert ----------------------------------
        await alert_repo.deactivate(alert.id, recipient.id)
        logger.info("Alert deactivated", alert_id=alert.id)

        # -- 3. Notify donor -----------------------------------------------
        donor_result = await notifier.notify_donor(
            alert=alert,
            recipient=recipient,
            donation_id=donation_id,
        )
        if donor_result.success:
            notifications_sent.append(f"donor:{alert.donor_id}:{notifier.channel}")
            logger.info("Donor notified", channel=notifier.channel)
        else:
            logger.warning("Donor notification failed", error=donor_result.error)

        # -- 4. Notify recipient -------------------------------------------
        recipient_result = await notifier.notify_recipient(
            alert=alert,
            recipient=recipient,
            donation_id=donation_id,
        )
        if recipient_result.success:
            notifications_sent.append(f"recipient:{recipient.id}:{notifier.channel}")
            logger.info("Recipient notified", channel=notifier.channel)
        else:
            logger.warning("Recipient notification failed", error=recipient_result.error)

        # -- 5. Ops summary (monitoring channel) --------------------------
        elapsed = time.time() - t_start
        await notifier.notify_agent_summary(
            alert=alert,
            recipient=recipient,
            donation_id=donation_id,
            distance_km=state.get("distance_km", 0.0),
            match_score=state.get("match_score", 0.0),
            coordination_seconds=elapsed,
        )

        steps.append("execute_node:completed")

        return {
            **state,
            "execution_status": "completed",
            "notifications_sent": notifications_sent,
            "steps_taken": steps,
            "errors": errors,
        }

    except Exception as exc:
        logger.error("Execute node failed", error=str(exc))
        errors.append(f"Execute error: {exc}")
        steps.append("execute_node:failed")
        return {
            **state,
            "execution_status": "failed",
            "notifications_sent": notifications_sent,
            "steps_taken": steps,
            "errors": errors,
        }
