"""Modelo de ruta logística."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .food_alert import GeoPoint


class RouteStep(BaseModel):
    order: int
    location: GeoPoint
    address: str
    action: str  # "pickup" | "delivery"
    contact_name: str
    contact_phone: str
    notes: str = ""


class Route(BaseModel):
    """Ruta optimizada para la entrega de donación."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    donation_id: str
    steps: list[RouteStep] = Field(default_factory=list)
    total_distance_km: float = 0.0
    estimated_duration_minutes: float = 0.0
    status: str = "planned"  # planned | active | completed
    volunteer_id: Optional[str] = None
    notes: str = ""
