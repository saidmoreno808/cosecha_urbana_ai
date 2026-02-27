"""Notificaciones via WhatsApp Business API (Meta)."""
import structlog
import httpx

from .base import NotificationResult, NotificationService
from ..config import get_settings
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient

logger = structlog.get_logger()


class WhatsAppNotificationService(NotificationService):
    """Envía mensajes via WhatsApp Business API."""

    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.whatsapp_api_token
        self.phone_id = settings.whatsapp_phone_id

    async def notify_donor(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        message = (
            f"[OK] *cosecha_urbana_ai*\n\n"
            f"Gracias {alert.donor_name}! Tu donacion fue coordinada:\n\n"
            f"[Alimento] {alert.food_category.value} - {alert.quantity_kg}kg\n"
            f"[Receptor] {recipient.name}\n"
            f"[Beneficiarios] {recipient.beneficiaries_count} personas\n"
            f"[Folio] {(donation_id or '')[:8].upper()}\n\n"
            f"Un voluntario pasara a recoger. Gracias por tu contribucion!"
        )
        phone = getattr(alert, "contact_phone", "")
        return await self._send_message(phone=phone, message=message)

    async def notify_recipient(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        message = (
            f"*cosecha_urbana_ai - Nueva Donacion*\n\n"
            f"Hola {recipient.contact_name}!\n\n"
            f"[Alimento] {alert.description}\n"
            f"[Cantidad] {alert.quantity_kg} kg\n"
            f"[Origen] {alert.donor_name}\n"
            f"[Vence en] {alert.hours_until_expiry:.1f} horas\n"
            f"[Folio] {(donation_id or '')[:8].upper()}\n\n"
            f"Por favor confirma disponibilidad respondiendo OK."
        )
        return await self._send_message(phone=recipient.contact_phone, message=message)

    async def _send_message(self, phone: str, message: str) -> NotificationResult:
        if not self.token or not self.phone_id or not phone:
            logger.info("WhatsApp not configured or no phone, skipping")
            return NotificationResult(success=False, channel="whatsapp", error="Not configured")

        phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/{self.phone_id}/messages",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_clean,
                        "type": "text",
                        "text": {"body": message},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    msg_id = data.get("messages", [{}])[0].get("id")
                    return NotificationResult(success=True, channel="whatsapp", message_id=msg_id)

                error = resp.text[:200]
                logger.error("WhatsApp API error", status=resp.status_code, error=error)
                return NotificationResult(success=False, channel="whatsapp", error=error)

        except Exception as exc:
            logger.error("WhatsApp send failed", error=str(exc))
            return NotificationResult(success=False, channel="whatsapp", error=str(exc))
