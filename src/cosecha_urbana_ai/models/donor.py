"""Modelo de donante (centros comerciales, restaurantes, supermercados)."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .food_alert import FoodCategory, GeoPoint


class OperatingHours(BaseModel):
    open: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Hora apertura HH:MM")
    close: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Hora cierre HH:MM")
    days: list[str] = Field(default_factory=list, description="Días de operación")


class Donor(BaseModel):
    """Donante de excedentes alimentarios."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    business_type: str = Field(..., description="restaurant, supermarket, food_court, etc.")
    contact_name: str
    contact_phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    contact_email: EmailStr

    # Ubicación
    location: GeoPoint
    address: str
    city: str = "Monterrey"
    state: str = "Nuevo León"

    # Capacidad y preferencias
    typical_food_categories: list[FoodCategory] = Field(default_factory=list)
    operating_hours: Optional[OperatingHours] = None
    has_refrigeration: bool = False
    average_kg_per_donation: float = Field(default=10.0, gt=0)

    # Estado
    is_active: bool = True
    is_verified: bool = False
    total_donations: int = 0
    total_kg_donated: float = 0.0

    # Metadata
    registered_at: Optional[str] = None
    notes: str = ""
    description_vector: Optional[list[float]] = None

    def to_es_doc(self) -> dict:
        doc = self.model_dump(mode="json", exclude={"id", "description_vector"})
        doc["location"] = {"lat": self.location.lat, "lon": self.location.lon}
        return doc
