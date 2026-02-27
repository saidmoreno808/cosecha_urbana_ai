"""Repositorio para donaciones coordinadas."""
from typing import Optional

import structlog
from elasticsearch import AsyncElasticsearch

from ...models.donation import Donation
from ...config import get_settings
from .base import BaseRepository

logger = structlog.get_logger()


class DonationRepository(BaseRepository):
    def __init__(self, es: AsyncElasticsearch) -> None:
        settings = get_settings()
        super().__init__(es, settings.donations_history_index)

    async def create(self, donation: Donation) -> Donation:
        doc = donation.to_es_doc()
        doc_id, _ = await super().create(doc, donation.id)
        donation.id = doc_id
        logger.info(
            "Donation recorded",
            donation_id=doc_id,
            donor=donation.donor_name,
            recipient=donation.recipient_name,
            kg=donation.quantity_kg,
        )
        return donation

    async def get_by_id(self, donation_id: str) -> Optional[Donation]:
        doc = await super().get_by_id(donation_id)
        if not doc:
            return None
        return Donation(**doc)

    async def get_recent(self, size: int = 20) -> list[Donation]:
        query = {
            "query": {"match_all": {}},
            "sort": [{"created_at": {"order": "desc"}}],
        }
        docs = await self.search(query, size=size)
        return [Donation(**d) for d in docs]

    async def mark_completed(self, donation_id: str, completed_at: str) -> None:
        await self.update(
            donation_id,
            {"status": "completed", "completed_at": completed_at},
        )
