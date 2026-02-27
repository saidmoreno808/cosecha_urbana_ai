"""Singleton cliente Elasticsearch con retry automático."""
import structlog
from elasticsearch import AsyncElasticsearch
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings

logger = structlog.get_logger()
_es_client: AsyncElasticsearch | None = None


def get_es_client() -> AsyncElasticsearch:
    """Singleton factory para el cliente ES Serverless (Elastic Cloud)."""
    global _es_client
    if _es_client is None:
        settings = get_settings()

        if settings.elastic_cloud_id:
            _es_client = AsyncElasticsearch(
                cloud_id=settings.elastic_cloud_id,
                api_key=settings.elasticsearch_api_key,
                request_timeout=30,
            )
        else:
            # Serverless - API key como base64
            _es_client = AsyncElasticsearch(
                hosts=[settings.elasticsearch_url],
                api_key=settings.elasticsearch_api_key,
                retry_on_timeout=True,
                max_retries=3,
                request_timeout=30,
            )

        logger.info(
            "Elasticsearch client initialized",
            url=settings.elasticsearch_url,
        )

    return _es_client


async def close_es_client() -> None:
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None
        logger.info("Elasticsearch client closed")


async def check_es_connection() -> dict:
    """Verifica la conexión y devuelve info del cluster."""
    es = get_es_client()
    info = await es.info()
    return {
        "cluster_name": info.get("cluster_name", "unknown"),
        "version": info.get("version", {}).get("number", "unknown"),
        "status": "connected",
    }
