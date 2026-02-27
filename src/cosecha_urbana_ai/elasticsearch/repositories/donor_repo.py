"""Repositorio para donantes."""
from typing import Optional

import structlog
from elasticsearch import AsyncElasticsearch

from ...models.donor import Donor
from ...config import get_settings
from .base import BaseRepository

logger = structlog.get_logger()


class DonorRepository(BaseRepository):
    def __init__(self, es: AsyncElasticsearch) -> None:
        settings = get_settings()
        super().__init__(es, settings.donors_index)

    async def create(self, donor: Donor) -> Donor:
        doc = donor.to_es_doc()
        doc_id, _ = await super().create(doc, donor.id)
        donor.id = doc_id
        logger.info("Donor created", donor_id=doc_id, name=donor.name)
        return donor

    async def get_by_id(self, donor_id: str) -> Optional[Donor]:
        doc = await super().get_by_id(donor_id)
        if not doc:
            return None
        return Donor(**doc)

    async def get_all_active(self, size: int = 100) -> list[Donor]:
        query = {"query": {"term": {"is_active": True}}}
        docs = await self.search(query, size=size)
        return [Donor(**d) for d in docs]

    async def update_donation_stats(self, donor_id: str, kg_donated: float) -> None:
        await self.es.update(
            index=self.index,
            id=donor_id,
            body={
                "script": {
                    "source": """
                        ctx._source.total_donations += 1;
                        ctx._source.total_kg_donated += params.kg;
                    """,
                    "params": {"kg": kg_donated},
                }
            },
            refresh="wait_for",
        )
