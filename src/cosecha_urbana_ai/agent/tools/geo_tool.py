"""Tool de búsqueda geoespacial en Elasticsearch."""
import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ...elasticsearch.client import get_es_client

logger = structlog.get_logger()


class GeoSearchInput(BaseModel):
    lat: float = Field(description="Latitud del punto central")
    lon: float = Field(description="Longitud del punto central")
    radius_km: float = Field(default=15.0, description="Radio de búsqueda en km")
    index: str = Field(description="Índice de Elasticsearch a buscar")


class GeoProximityTool(BaseTool):
    """Busca documentos dentro de un radio geográfico ordenados por distancia."""

    name: str = "geo_proximity_search"
    description: str = (
        "Busca en Elasticsearch documentos dentro de un radio geográfico. "
        "Devuelve resultados ordenados por distancia. "
        "Úsalo para encontrar receptores o donantes cercanos a una ubicación."
    )
    args_schema: type[BaseModel] = GeoSearchInput

    async def _arun(self, lat: float, lon: float, radius_km: float, index: str) -> str:
        es = get_es_client()
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"is_active": True}},
                        {
                            "geo_distance": {
                                "distance": f"{radius_km}km",
                                "location": {"lat": lat, "lon": lon},
                            }
                        },
                    ]
                }
            },
            "sort": [
                {
                    "_geo_distance": {
                        "location": {"lat": lat, "lon": lon},
                        "order": "asc",
                        "unit": "km",
                    }
                }
            ],
            "size": 10,
        }

        try:
            result = await es.search(index=index, body=query)
            hits = result["hits"]["hits"]
            if not hits:
                return f"No results within {radius_km}km"

            output = f"Found {len(hits)} results:\n"
            for hit in hits:
                src = hit["_source"]
                dist = hit.get("sort", [0])[0]
                output += f"- {src.get('name', 'Unknown')} ({dist:.2f}km) ID: {hit['_id']}\n"
            return output

        except Exception as exc:
            logger.error("Geo tool error", error=str(exc))
            return f"Geo search error: {exc}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")
