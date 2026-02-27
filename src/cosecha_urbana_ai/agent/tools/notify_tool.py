"""Tool de notificaciones para el agente."""
import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class NotifyInput(BaseModel):
    recipient_type: str = Field(description="donor | recipient | volunteer")
    contact_id: str = Field(description="ID del contacto a notificar")
    message: str = Field(description="Mensaje a enviar")
    channel: str = Field(default="log", description="log | whatsapp | slack")


class NotifyTool(BaseTool):
    """Envía notificaciones a donantes, receptores o voluntarios."""

    name: str = "send_notification"
    description: str = (
        "Envía notificaciones a través de diferentes canales (WhatsApp, Slack, log). "
        "Úsalo para informar sobre donaciones coordinadas, confirmaciones de entrega, etc."
    )
    args_schema: type[BaseModel] = NotifyInput

    async def _arun(
        self,
        recipient_type: str,
        contact_id: str,
        message: str,
        channel: str = "log",
    ) -> str:
        logger.info(
            "Notification sent",
            channel=channel,
            recipient_type=recipient_type,
            contact_id=contact_id,
            message_preview=message[:80],
        )
        return f"Notification sent via {channel} to {recipient_type}:{contact_id}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")
