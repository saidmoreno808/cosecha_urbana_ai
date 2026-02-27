"""Tool de búsqueda general en Elasticsearch."""
import json
import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ...elasticsearch.client import get_es_client

logger = structlog.get_logger()


class ESSearchInput(BaseModel):
    index: str = Field(description="Elasticsearch index name")
    query: str = Field(description="JSON string with the ES query DSL")
    size: int = Field(default=10, description="Max results to return")


class ESSearchTool(BaseTool):
    """Búsqueda general en Elasticsearch con query DSL."""

    name: str = "elasticsearch_search"
    description: str = (
        "Busca documentos en Elasticsearch usando query DSL. "
        "Proporciona el índice y la query como JSON string. "
        "Úsalo para búsquedas de texto completo, filtros por campo, etc."
    )
    args_schema: type[BaseModel] = ESSearchInput

    async def _arun(self, index: str, query: str, size: int = 10) -> str:
        es = get_es_client()
        try:
            query_body = json.loads(query)
            result = await es.search(index=index, body=query_body, size=size)
            hits = result["hits"]["hits"]

            if not hits:
                return "No results found."

            output = f"Found {result['hits']['total']['value']} total, showing {len(hits)}:\n"
            for hit in hits:
                src = hit["_source"]
                name = src.get("name", src.get("donor_name", hit["_id"]))
                output += f"- [{hit['_id']}] {name}\n"
            return output

        except json.JSONDecodeError as exc:
            return f"Invalid JSON query: {exc}"
        except Exception as exc:
            logger.error("Search tool error", error=str(exc))
            return f"Search error: {exc}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")
