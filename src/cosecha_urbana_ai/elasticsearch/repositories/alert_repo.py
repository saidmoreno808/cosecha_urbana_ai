"""Repositorio para alertas de excedente alimentario."""
from typing import Optional
import structlog
from elasticsearch import AsyncElasticsearch

from ...models.food_alert import FoodAlert, UrgencyLevel
from ...config import get_settings
from .base import BaseRepository

logger = structlog.get_logger()


class AlertRepository(BaseRepository):
    def __init__(self, es: AsyncElasticsearch) -> None:
        settings = get_settings()
        super().__init__(es, settings.food_alerts_index)

    async def create(self, alert: FoodAlert) -> FoodAlert:
        doc = alert.to_es_doc()
        doc_id, _ = await super().create(doc, alert.id)
        alert.id = doc_id
        logger.info(
            "Alert created",
            alert_id=doc_id,
            donor=alert.donor_name,
            category=alert.food_category,
        )
        return alert

    async def get_by_id(self, alert_id: str) -> Optional[FoodAlert]:
        doc = await super().get_by_id(alert_id)
        if not doc:
            return None
        return FoodAlert(**doc)

    async def find_active_near(
        self,
        lat: float,
        lon: float,
        max_km: float = 15.0,
        size: int = 20,
    ) -> list[FoodAlert]:
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"is_active": True}},
                        {
                            "geo_distance": {
                                "distance": f"{max_km}km",
                                "location": {"lat": lat, "lon": lon},
                            }
                        },
                    ]
                }
            },
            "sort": [{"urgency_score": {"order": "desc"}}, {"expiry_datetime": {"order": "asc"}}],
        }
        docs = await self.search(query, size=size)
        return [FoodAlert(**d) for d in docs]

    async def find_active(self, size: int = 50) -> list[FoodAlert]:
        query = {
            "query": {"term": {"is_active": True}},
            "sort": [{"urgency_score": {"order": "desc"}}],
        }
        docs = await self.search(query, size=size)
        return [FoodAlert(**d) for d in docs]

    async def deactivate(self, alert_id: str, recipient_id: str) -> None:
        await self.update(
            alert_id,
            {"is_active": False, "matched_recipient_id": recipient_id},
        )
