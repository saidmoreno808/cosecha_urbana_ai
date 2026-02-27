"""Abstract notifier base class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient


@dataclass
class NotificationResult:
    success: bool
    channel: str
    message_id: str | None = None
    error: str | None = None


class NotificationService(ABC):
    """Interfaz base para servicios de notificación."""

    @abstractmethod
    async def notify_donor(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult: ...

    @abstractmethod
    async def notify_recipient(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult: ...
