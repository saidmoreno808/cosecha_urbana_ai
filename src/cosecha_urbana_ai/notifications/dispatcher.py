"""
Notification Dispatcher.

Selects the right notification channel based on configuration:
  1. KibanaConnector  - if KIBANA_SLACK_CONNECTOR_ID is set (Elastic-native, recommended)
  2. SlackWebhook     - if SLACK_WEBHOOK_URL is set (direct webhook, simple)
  3. LogOnly          - fallback when no notification service is configured

Usage in execute_node:
    from ...notifications.dispatcher import NotificationDispatcher
    notifier = NotificationDispatcher()
    result = await notifier.notify_agent_summary(...)
"""
import structlog

from ..config import get_settings
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient
from .base import NotificationResult, NotificationService
from .kibana_connector import KibanaConnectorNotifier
from .slack_webhook import SlackWebhookNotifier

logger = structlog.get_logger()


class LogOnlyNotifier(NotificationService):
    """Fallback notifier: just logs. Used when no service is configured."""

    async def notify_donor(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        logger.info(
            "LOG_ONLY | Donor notification",
            donor=alert.donor_name,
            recipient=recipient.name,
            kg=alert.quantity_kg,
            donation_id=donation_id[:8],
        )
        return NotificationResult(success=True, channel="log_only")

    async def notify_recipient(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        logger.info(
            "LOG_ONLY | Recipient notification",
            recipient=recipient.name,
            donor=alert.donor_name,
            kg=alert.quantity_kg,
            donation_id=donation_id[:8],
        )
        return NotificationResult(success=True, channel="log_only")


class NotificationDispatcher:
    """
    Auto-selects notification service based on .env configuration.

    Priority:
      1. Kibana Connector (KIBANA_SLACK_CONNECTOR_ID + KIBANA_URL)
      2. Slack Webhook (SLACK_WEBHOOK_URL)
      3. Log Only (no config - always works, useful for dev/demo)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._notifier: NotificationService
        self._channel: str

        if settings.kibana_slack_connector_id and settings.kibana_url:
            self._notifier = KibanaConnectorNotifier()
            self._channel = "kibana_connector"
            logger.info("Notification channel: Kibana Connector (Elastic-native)")

        elif settings.slack_webhook_url:
            self._notifier = SlackWebhookNotifier()
            self._channel = "slack_webhook"
            logger.info("Notification channel: Slack Incoming Webhook")

        else:
            self._notifier = LogOnlyNotifier()
            self._channel = "log_only"
            logger.info(
                "No notification service configured - using log only. "
                "Set SLACK_WEBHOOK_URL or KIBANA_SLACK_CONNECTOR_ID in .env to enable Slack."
            )

    @property
    def channel(self) -> str:
        return self._channel

    async def notify_donor(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        return await self._notifier.notify_donor(alert, recipient, donation_id)

    async def notify_recipient(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        return await self._notifier.notify_recipient(alert, recipient, donation_id)

    async def notify_agent_summary(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        donation_id: str,
        distance_km: float,
        match_score: float,
        coordination_seconds: float,
    ) -> NotificationResult:
        """
        Post a real-time ops summary after every agent run.
        Works for both Kibana Connector and Slack Webhook.
        """
        if isinstance(self._notifier, KibanaConnectorNotifier):
            return await self._notifier.notify_agent_summary(
                donor_name=alert.donor_name,
                recipient_name=recipient.name,
                quantity_kg=alert.quantity_kg,
                distance_km=distance_km,
                match_score=match_score,
                coordination_seconds=coordination_seconds,
                donation_id=donation_id,
            )

        if isinstance(self._notifier, SlackWebhookNotifier):
            return await self._notifier.notify_agent_summary(
                alert_id=alert.id or "",
                donor_name=alert.donor_name,
                recipient_name=recipient.name,
                quantity_kg=alert.quantity_kg,
                distance_km=distance_km,
                urgency_level=alert.urgency_level.value,
                match_score=match_score,
                coordination_seconds=coordination_seconds,
                donation_id=donation_id,
            )

        # LogOnly fallback
        logger.info(
            "AGENT_SUMMARY",
            donor=alert.donor_name,
            recipient=recipient.name,
            kg=alert.quantity_kg,
            distance_km=distance_km,
            match_score=match_score,
            seconds=coordination_seconds,
        )
        return NotificationResult(success=True, channel="log_only")
