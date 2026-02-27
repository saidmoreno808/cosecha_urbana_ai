"""Modelo de alerta de excedente alimentario."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FoodCategory(str, Enum):
    PREPARED = "prepared"      # Comida preparada (más urgente)
    BAKERY = "bakery"
    PRODUCE = "produce"        # Frutas y verduras
    DAIRY = "dairy"
    MEAT = "meat"
    DRY_GOODS = "dry_goods"    # Granos, enlatados (menos urgente)


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"      # < 2 horas
    HIGH = "high"              # 2-4 horas
    MEDIUM = "medium"          # 4-12 horas
    LOW = "low"                # > 12 horas


class GeoPoint(BaseModel):
    """Punto geográfico con latitud y longitud."""
    lat: float = Field(..., ge=-90, le=90, description="Latitud")
    lon: float = Field(..., ge=-180, le=180, description="Longitud")


class FoodAlert(BaseModel):
    """Alerta de excedente alimentario generada por un donante."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    donor_id: str
    donor_name: str
    food_category: FoodCategory
    description: str = Field(..., min_length=10, max_length=500)
    quantity_kg: float = Field(..., gt=0, le=1000)

    # Tiempo de vida
    expiry_datetime: datetime
    alert_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Geolocalización
    location: GeoPoint
    address: str

    # Estado
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    is_active: bool = True
    matched_recipient_id: Optional[str] = None

    # Metadata
    special_requirements: list[str] = Field(default_factory=list)
    contact_phone: str = ""

    @field_validator("expiry_datetime")
    @classmethod
    def expiry_must_be_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError("Expiry datetime must be in the future")
        return v

    @property
    def hours_until_expiry(self) -> float:
        now = datetime.now(timezone.utc)
        expiry = self.expiry_datetime
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        delta = expiry - now
        return max(0.0, delta.total_seconds() / 3600)

    def compute_urgency(self) -> UrgencyLevel:
        hours = self.hours_until_expiry
        if hours < 2:
            return UrgencyLevel.CRITICAL
        elif hours < 4:
            return UrgencyLevel.HIGH
        elif hours < 12:
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.LOW

    def to_es_doc(self) -> dict:
        """Serializa para indexar en Elasticsearch."""
        doc = self.model_dump(mode="json", exclude={"id"})
        # ES usa geo_point como {"lat": ..., "lon": ...}
        doc["location"] = {"lat": self.location.lat, "lon": self.location.lon}
        doc["hours_until_expiry"] = self.hours_until_expiry
        doc["urgency_score"] = self._compute_urgency_score()
        doc["@timestamp"] = doc["alert_created_at"]
        return doc

    def _compute_urgency_score(self) -> float:
        hours = self.hours_until_expiry
        time_urgency = max(0.0, min(1.0, 1.0 - (hours / 24.0)))
        category_weights = {
            "prepared": 1.0, "dairy": 0.85, "meat": 0.9,
            "bakery": 0.8, "produce": 0.7, "dry_goods": 0.3,
        }
        return time_urgency * category_weights.get(self.food_category.value, 0.5)
