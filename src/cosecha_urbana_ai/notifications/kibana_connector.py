"""
Kibana Actions Connector Notifier (Elastic-native notifications).

Uses Kibana's built-in Slack connector via the Actions API.
This is the recommended approach for the hackathon as it demonstrates
MORE Elastic ecosystem usage.

How it works:
  1. Create a Slack connector in Kibana (using a Slack Incoming Webhook URL)
  2. Kibana stores the webhook URL as a secured connector
  3. The agent calls Kibana's Actions API to fire the notification
  4. Kibana sends the message to Slack on behalf of the agent

Setup:
  Option A - Via Kibana UI:
    Stack Management -> Connectors -> Create connector -> Slack API
    (or "Slack" for webhook-based connector)
    Copy the connector ID -> KIBANA_SLACK_CONNECTOR_ID in .env

  Option B - Via this script (auto-creates the connector):
    python scripts/setup_kibana_connector.py

Docs: https://www.elastic.co/guide/en/kibana/current/slack-action-type.html
"""
import httpx
import structlog

from ..config import get_settings
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient
from .base import NotificationResult, NotificationService

logger = structlog.get_logger()


class KibanaConnectorNotifier(NotificationService):
    """
    Fires Kibana Actions (Slack connector) via the Kibana Actions API.
    Demonstrates Elastic-native notification pipeline.

    Endpoint: POST /api/actions/connector/{connector_id}/_execute
    """

    EXECUTE_URL = "/api/actions/connector/{connector_id}/_execute"

    def __init__(self) -> None:
        settings = get_settings()
        self.kibana_url = settings.kibana_url.rstrip("/") if settings.kibana_url else ""
        self.api_key = settings.elasticsearch_api_key
        self.connector_id = settings.kibana_slack_connector_id
        self._enabled = bool(self.kibana_url and self.connector_id)

    def _headers(self) -> dict:
        return {
            "kbn-xsrf": "true",
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _execute_connector(self, message: str) -> NotificationResult:
        if not self._enabled:
            logger.info("Kibana connector not configured, skipping")
            return NotificationResult(
                success=False,
                channel="kibana_connector",
                error="KIBANA_SLACK_CONNECTOR_ID not set",
            )

        url = self.kibana_url + self.EXECUTE_URL.format(connector_id=self.connector_id)

        # Kibana .slack connector (Incoming Webhook) execute format
        # The .slack connector uses {params: {message: "..."}} - not subAction
        payload = {
            "params": {
                "message": message,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                response = await client.post(url, json=payload, headers=self._headers())

            if response.status_code in (200, 204):
                logger.info("Kibana connector notification sent", connector=self.connector_id)
                return NotificationResult(success=True, channel="kibana_connector")
            else:
                error = f"HTTP {response.status_code}: {response.text[:300]}"
                logger.warning("Kibana connector failed", error=error)
                return NotificationResult(success=False, channel="kibana_connector", error=error)

        except Exception as exc:
            logger.error("Kibana connector error", error=str(exc))
            return NotificationResult(success=False, channel="kibana_connector", error=str(exc))

    async def notify_donor(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        donation_id: str,
    ) -> NotificationResult:
        message = (
            f"*cosecha_urbana_ai | Donation Confirmed*\n"
            f"Donor: {alert.donor_name}\n"
            f"Food: {alert.food_category.value} - {alert.quantity_kg} kg\n"
            f"Matched to: {recipient.name}\n"
            f"Urgency: {alert.urgency_level.value} | "
            f"Expires in: {alert.hours_until_expiry:.1f}h\n"
            f"ID: `{donation_id[:8].upper()}`"
        )
        return await self._execute_connector(message)

    async def notify_recipient(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        donation_id: str,
    ) -> NotificationResult:
        message = (
            f"*cosecha_urbana_ai | Incoming Donation*\n"
            f"To: {recipient.name} ({recipient.contact_name})\n"
            f"Food: {alert.description[:60]} - {alert.quantity_kg} kg\n"
            f"From: {alert.donor_name}\n"
            f"Address: {alert.address}\n"
            f"Must receive within: {alert.hours_until_expiry:.1f}h\n"
            f"ID: `{donation_id[:8].upper()}`"
        )
        return await self._execute_connector(message)

    async def notify_agent_summary(
        self,
        donor_name: str,
        recipient_name: str,
        quantity_kg: float,
        distance_km: float,
        match_score: float,
        coordination_seconds: float,
        donation_id: str,
    ) -> NotificationResult:
        """Post agent run summary to the ops Slack channel."""
        message = (
            f"*cosecha_urbana_ai | Agent Run Complete*\n"
            f"Matched {quantity_kg} kg: {donor_name} -> {recipient_name}\n"
            f"Distance: {distance_km:.1f} km | "
            f"Match score: {match_score:.0%} | "
            f"Time: {coordination_seconds:.1f}s\n"
            f"Donation ID: `{donation_id[:8].upper()}`"
        )
        return await self._execute_connector(message)


async def create_kibana_slack_connector(webhook_url: str) -> str | None:
    """
    Utility: Creates a Slack connector in Kibana via API.
    Returns the connector ID if successful.

    Call once during setup - saves the ID as KIBANA_SLACK_CONNECTOR_ID.
    """
    settings = get_settings()
    if not settings.kibana_url:
        logger.error("KIBANA_URL not set")
        return None

    url = settings.kibana_url.rstrip("/") + "/api/actions/connector"
    headers = {
        "kbn-xsrf": "true",
        "Authorization": f"ApiKey {settings.elasticsearch_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": "cosecha_urbana_ai - Slack",
        "connector_type_id": ".slack_api",
        "config": {},
        "secrets": {"token": webhook_url},
    }

    # .slack connector: webhookUrl must go in secrets (not config)
    payload_webhook = {
        "name": "cosecha_urbana_ai - Slack Webhook",
        "connector_type_id": ".slack",
        "config": {},
        "secrets": {"webhookUrl": webhook_url},
    }

    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        response = await client.post(url, json=payload_webhook, headers=headers)

    if response.status_code in (200, 201):
        data = response.json()
        connector_id = data.get("id", "")
        logger.info("Kibana Slack connector created", id=connector_id)
        print(f"\nConnector created! Add to .env:\nKIBANA_SLACK_CONNECTOR_ID={connector_id}\n")
        return connector_id
    else:
        logger.error(
            "Failed to create Kibana connector",
            status=response.status_code,
            body=response.text[:300],
        )
        return None
