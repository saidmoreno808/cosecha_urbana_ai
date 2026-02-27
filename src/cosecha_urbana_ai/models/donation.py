"""Modelo de donación completada."""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .food_alert import GeoPoint, FoodCategory, UrgencyLevel


class Donation(BaseModel):
    """Registro de una donación coordinada por el agente."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    alert_id: str
    donor_id: str
    donor_name: str
    recipient_id: str
    recipient_name: str
    food_category: FoodCategory
    quantity_kg: float
    distance_km: float
    urgency_level: UrgencyLevel
    status: str = Field(
        default="in_progress",
        description="pending | in_progress | completed | cancelled | failed"
    )
    coordination_time_minutes: Optional[float] = None
    pickup_location: GeoPoint
    delivery_location: GeoPoint
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None
    beneficiaries_served: int = 0
    agent_reasoning: str = ""
    match_score: float = 0.0

    def to_es_doc(self) -> dict:
        doc = self.model_dump(mode="json", exclude={"id"})
        doc["pickup_location"] = {
            "lat": self.pickup_location.lat,
            "lon": self.pickup_location.lon,
        }
        doc["delivery_location"] = {
            "lat": self.delivery_location.lat,
            "lon": self.delivery_location.lon,
        }
        doc["@timestamp"] = doc["created_at"]
        return doc
