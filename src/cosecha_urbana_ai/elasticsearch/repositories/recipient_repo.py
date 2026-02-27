"""Repositorio para receptores de donaciones."""
from typing import Optional

import structlog
from elasticsearch import AsyncElasticsearch

from ...models.food_alert import FoodCategory
from ...models.recipient import Recipient
from ...config import get_settings
from .base import BaseRepository

logger = structlog.get_logger()


class RecipientRepository(BaseRepository):
    def __init__(self, es: AsyncElasticsearch) -> None:
        settings = get_settings()
        super().__init__(es, settings.recipients_index)

    async def create(self, recipient: Recipient) -> Recipient:
        doc = recipient.to_es_doc()
        doc_id, _ = await super().create(doc, recipient.id)
        recipient.id = doc_id
        return recipient

    async def get_by_id(self, recipient_id: str) -> Optional[Recipient]:
        doc = await super().get_by_id(recipient_id)
        if not doc:
            return None
        return Recipient(**doc)

    async def find_compatible_recipients(
        self,
        lat: float,
        lon: float,
        max_km: float,
        food_category: FoodCategory,
        quantity_kg: float,
        requires_refrigeration: bool = False,
        size: int = 10,
    ) -> list[Recipient]:
        """
        Busca receptores compatibles combinando:
        - Filtro geográfico por distancia
        - Compatibilidad de categoría de alimento
        - Capacidad de almacenamiento si se requiere refrigeración
        """
        must_filters = [
            {"term": {"is_active": True}},
            {"term": {"is_verified": True}},
            {
                "geo_distance": {
                    "distance": f"{max_km}km",
                    "location": {"lat": lat, "lon": lon},
                }
            },
            {"term": {"accepted_food_categories": food_category.value}},
        ]

        if requires_refrigeration:
            must_filters.append(
                {"range": {"storage_capacity.refrigerated_kg": {"gte": quantity_kg * 0.5}}}
            )

        query = {
            "query": {"bool": {"filter": must_filters}},
            "sort": [
                {
                    "_geo_distance": {
                        "location": {"lat": lat, "lon": lon},
                        "order": "asc",
                        "unit": "km",
                    }
                },
                {"current_need_level": {"order": "desc"}},
            ],
        }

        docs = await self.search(query, size=size)

        recipients = []
        for doc in docs:
            r = Recipient(**doc)
            # Extraer distancia del sort
            if "_sort" in doc:
                r.distance_km = float(doc["_sort"][0])
            recipients.append(r)

        return recipients

    async def get_all_active(self, size: int = 100) -> list[Recipient]:
        query = {"query": {"term": {"is_active": True}}}
        docs = await self.search(query, size=size)
        return [Recipient(**d) for d in docs]

    async def update_stats(self, recipient_id: str, kg_received: float) -> None:
        await self.es.update(
            index=self.index,
            id=recipient_id,
            body={
                "script": {
                    "source": """
                        ctx._source.total_donations_received += 1;
                        ctx._source.total_kg_received += params.kg;
                    """,
                    "params": {"kg": kg_received},
                }
            },
            refresh="wait_for",
        )
