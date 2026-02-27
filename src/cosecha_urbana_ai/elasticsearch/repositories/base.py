"""Repositorio base con operaciones CRUD genéricas."""
from typing import Any, Optional, TypeVar
import uuid

import structlog
from elasticsearch import AsyncElasticsearch

logger = structlog.get_logger()

T = TypeVar("T")


class BaseRepository:
    """Repositorio base para operaciones ES."""

    def __init__(self, es: AsyncElasticsearch, index: str) -> None:
        self.es = es
        self.index = index

    async def get_by_id(self, doc_id: str) -> Optional[dict]:
        try:
            result = await self.es.get(index=self.index, id=doc_id)
            doc = result["_source"]
            doc["id"] = result["_id"]
            return doc
        except Exception as e:
            logger.warning("Document not found", index=self.index, id=doc_id, error=str(e))
            return None

    async def create(self, doc: dict, doc_id: Optional[str] = None) -> tuple[str, dict]:
        """Crea un documento. Devuelve (id, source)."""
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        result = await self.es.index(
            index=self.index,
            id=doc_id,
            document=doc,
            refresh="wait_for",
        )
        return result["_id"], doc

    async def update(self, doc_id: str, updates: dict) -> None:
        await self.es.update(
            index=self.index,
            id=doc_id,
            body={"doc": updates},
            refresh="wait_for",
        )

    async def delete(self, doc_id: str) -> None:
        await self.es.delete(index=self.index, id=doc_id, refresh="wait_for")

    async def search(self, query: dict, size: int = 20) -> list[dict]:
        result = await self.es.search(index=self.index, body=query, size=size)
        hits = result["hits"]["hits"]
        docs = []
        for hit in hits:
            doc = hit["_source"]
            doc["id"] = hit["_id"]
            if "sort" in hit:
                doc["_sort"] = hit["sort"]
            docs.append(doc)
        return docs

    async def count(self, query: Optional[dict] = None) -> int:
        body = query or {"query": {"match_all": {}}}
        result = await self.es.count(index=self.index, body=body)
        return result["count"]
