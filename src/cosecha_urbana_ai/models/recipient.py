"""Modelo de receptor (refugios, casas del migrante, asilos, orfanatos)."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .food_alert import FoodCategory, GeoPoint


class StorageCapacity(BaseModel):
    refrigerated_kg: float = 0.0
    frozen_kg: float = 0.0
    dry_kg: float = 0.0


class Recipient(BaseModel):
    """Receptor de donaciones alimentarias."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    organization_type: str = Field(
        ...,
        description="migrant_house, elderly_shelter, orphanage, food_bank, community_kitchen"
    )
    contact_name: str
    contact_phone: str
    contact_email: EmailStr

    # Ubicación
    location: GeoPoint
    address: str
    city: str = "Monterrey"
    state: str = "Nuevo León"

    # Capacidad y necesidades
    beneficiaries_count: int = Field(..., gt=0)
    accepted_food_categories: list[FoodCategory] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    storage_capacity: StorageCapacity = Field(default_factory=StorageCapacity)

    # Disponibilidad
    receiving_hours_start: str = "08:00"
    receiving_hours_end: str = "20:00"
    available_days: list[str] = Field(
        default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday"]
    )

    # Estado
    is_active: bool = True
    is_verified: bool = True
    current_need_level: str = Field(
        default="medium",
        description="low | medium | high | critical"
    )

    # Historial
    total_donations_received: int = 0
    total_kg_received: float = 0.0

    # Para matching semántico
    needs_description: str = ""
    needs_vector: Optional[list[float]] = None

    # Campo calculado (no en DB)
    distance_km: Optional[float] = None

    def to_es_doc(self) -> dict:
        doc = self.model_dump(
            mode="json",
            exclude={"id", "needs_vector", "distance_km"}
        )
        doc["location"] = {"lat": self.location.lat, "lon": self.location.lon}
        return doc
