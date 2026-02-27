"""FastAPI dependency injection."""
from elasticsearch import AsyncElasticsearch
from ..elasticsearch.client import get_es_client as _get_es_client


def get_es() -> AsyncElasticsearch:
    """Dependency: Elasticsearch client."""
    return _get_es_client()
