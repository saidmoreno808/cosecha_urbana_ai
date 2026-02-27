"""
Slack Incoming Webhook Notifier.

Uses a Slack Incoming Webhook URL - no bot token, no OAuth, no scopes.
Just a single POST request. This is the simplest Slack integration.

Setup (5 minutes):
  1. Go to https://api.slack.com/apps -> Create App -> From scratch
  2. App name: "Cosecha Urbana AI"  -> Select your workspace -> Create
  3. Left sidebar -> "Incoming Webhooks" -> Toggle ON
  4. Click "Add New Webhook to Workspace" -> Select #cosecha-urbana channel
  5. Copy the Webhook URL -> paste as SLACK_WEBHOOK_URL in .env

Message format uses Slack Block Kit for rich notifications.
"""
import httpx
import structlog

from .base import NotificationResult, NotificationService
from ..config import get_settings
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient

logger = structlog.get_logger()


def _urgency_emoji(urgency_level: str) -> str:
    return {
        "critical": ":rotating_light:",
        "high":     ":orange_circle:",
        "medium":   ":yellow_circle:",
        "low":      ":green_circle:",
    }.get(urgency_level, ":white_circle:")


def _category_emoji(food_category: str) -> str:
    return {
        "prepared":  ":plate_with_cutlery:",
        "bakery":    ":bread:",
        "produce":   ":leafy_green:",
        "dairy":     ":milk_glass:",
        "meat":      ":meat_on_bone:",
        "dry_goods": ":rice:",
    }.get(food_category, ":fork_and_knife:")


class SlackWebhookNotifier(NotificationService):
    """
    Sends rich Block Kit notifications to a Slack channel via Incoming Webhook.

    One webhook URL -> one channel. No tokens, no permissions setup beyond
    installing the webhook to a workspace channel.
    """

    def __init__(self, webhook_url: str | None = None) -> None:
        settings = get_settings()
        self.webhook_url = webhook_url or settings.slack_webhook_url
        self._enabled = bool(self.webhook_url)

    async def notify_donor(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        donation_id: str,
    ) -> NotificationResult:
        """Notify the food donor that their surplus has been matched."""
        if not self._enabled:
            logger.info("Slack webhook not configured, skipping donor notification")
            return NotificationResult(success=False, channel="slack", error="Not configured")

        urgency_emoji = _urgency_emoji(alert.urgency_level.value)
        cat_emoji = _category_emoji(alert.food_category.value)
        short_id = donation_id[:8].upper()

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Cosecha Urbana AI - Donation Confirmed #{short_id}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Thank you, {alert.donor_name}!* :raised_hands:\n"
                        f"Your food surplus has been matched and a volunteer is on the way."
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"{cat_emoji} *Food:*\n{alert.food_category.value.title()} - {alert.description[:60]}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f":scales: *Quantity:*\n{alert.quantity_kg} kg",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f":house_with_garden: *Recipient:*\n{recipient.name}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f":busts_in_silhouette: *People served:*\n"
                            f"~{recipient.beneficiaries_count} beneficiaries"
                        ),
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"{urgency_emoji} *Urgency:*\n{alert.urgency_level.value.title()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f":stopwatch: *Expires in:*\n"
                            f"{alert.hours_until_expiry:.1f} hours"
                        ),
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Donation ID: `{donation_id}` | Powered by *cosecha_urbana_ai*",
                    }
                ],
            },
        ]

        return await self._post(blocks, text=f"Donation confirmed: {alert.quantity_kg}kg to {recipient.name}")

    async def notify_recipient(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        donation_id: str,
    ) -> NotificationResult:
        """Notify the recipient organization that food is incoming."""
        if not self._enabled:
            logger.info("Slack webhook not configured, skipping recipient notification")
            return NotificationResult(success=False, channel="slack", error="Not configured")

        urgency_emoji = _urgency_emoji(alert.urgency_level.value)
        cat_emoji = _category_emoji(alert.food_category.value)
        short_id = donation_id[:8].upper()

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Cosecha Urbana AI - Incoming Donation #{short_id}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Hello *{recipient.contact_name}* :wave:\n"
                        f"Food is on its way to *{recipient.name}*. "
                        f"Please have someone ready to receive."
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"{cat_emoji} *Food type:*\n{alert.description[:80]}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f":scales: *Amount:*\n{alert.quantity_kg} kg",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f":convenience_store: *From:*\n{alert.donor_name}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f":round_pushpin: *Address:*\n{alert.address}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"{urgency_emoji} *Urgency:*\n{alert.urgency_level.value.title()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            f":stopwatch: *Must pick up within:*\n"
                            f"{alert.hours_until_expiry:.1f} hours"
                        ),
                    },
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Confirm Receipt", "emoji": True},
                        "style": "primary",
                        "value": f"confirm_{donation_id}",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Donation ID: `{donation_id}` | Powered by *cosecha_urbana_ai*",
                    }
                ],
            },
        ]

        return await self._post(
            blocks,
            text=f"Incoming donation: {alert.quantity_kg}kg from {alert.donor_name}",
        )

    async def notify_agent_summary(
        self,
        alert_id: str,
        donor_name: str,
        recipient_name: str,
        quantity_kg: float,
        distance_km: float,
        urgency_level: str,
        match_score: float,
        coordination_seconds: float,
        donation_id: str,
    ) -> NotificationResult:
        """
        Post a summary of the agent's work to the ops channel.
        Useful for monitoring the agent in real time.
        """
        if not self._enabled:
            return NotificationResult(success=False, channel="slack", error="Not configured")

        urgency_emoji = _urgency_emoji(urgency_level)
        efficiency_bar = round(match_score * 10)
        match_bar = ":large_green_square:" * efficiency_bar + ":white_large_square:" * (10 - efficiency_bar)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "cosecha_urbana_ai - Agent Run Complete",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f":fork_and_knife: *Donor:*\n{donor_name}"},
                    {"type": "mrkdwn", "text": f":house: *Recipient:*\n{recipient_name}"},
                    {"type": "mrkdwn", "text": f":scales: *Amount:*\n{quantity_kg} kg"},
                    {"type": "mrkdwn", "text": f":straight_ruler: *Distance:*\n{distance_km:.2f} km"},
                    {"type": "mrkdwn", "text": f"{urgency_emoji} *Urgency:*\n{urgency_level.title()}"},
                    {
                        "type": "mrkdwn",
                        "text": f":zap: *Coordination time:*\n{coordination_seconds:.1f}s",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Match quality:* {match_bar} `{match_score:.0%}`",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Alert `{alert_id[:8]}` | Donation `{donation_id[:8]}` | *cosecha_urbana_ai*",
                    }
                ],
            },
        ]

        return await self._post(
            blocks,
            text=f"Agent matched {quantity_kg}kg: {donor_name} -> {recipient_name} ({distance_km:.1f}km, {coordination_seconds:.0f}s)",
        )

    async def _post(self, blocks: list, text: str = "") -> NotificationResult:
        """POST blocks to Slack Incoming Webhook."""
        payload = {"text": text, "blocks": blocks}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code == 200 and response.text == "ok":
                logger.info("Slack notification sent", text=text[:60])
                return NotificationResult(success=True, channel="slack")
            else:
                error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning("Slack notification failed", error=error)
                return NotificationResult(success=False, channel="slack", error=error)

        except httpx.TimeoutException:
            logger.warning("Slack notification timed out")
            return NotificationResult(success=False, channel="slack", error="Timeout")
        except Exception as exc:
            logger.error("Slack notification error", error=str(exc))
            return NotificationResult(success=False, channel="slack", error=str(exc))


