"""Queries de búsqueda geoespacial para Elasticsearch."""


def build_geo_distance_filter(
    lat: float,
    lon: float,
    radius_km: float,
) -> dict:
    """Filtro de distancia geográfica."""
    return {
        "geo_distance": {
            "distance": f"{radius_km}km",
            "location": {"lat": lat, "lon": lon},
        }
    }


def build_geo_sort(lat: float, lon: float, unit: str = "km") -> list[dict]:
    """Sort por distancia geográfica ascendente."""
    return [
        {
            "_geo_distance": {
                "location": {"lat": lat, "lon": lon},
                "order": "asc",
                "unit": unit,
            }
        }
    ]


def build_recipients_geo_query(
    lat: float,
    lon: float,
    radius_km: float,
    food_category: str,
    size: int = 10,
) -> dict:
    """Query completa para buscar receptores compatibles por geo + categoría."""
    return {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"is_active": True}},
                    {"term": {"accepted_food_categories": food_category}},
                    build_geo_distance_filter(lat, lon, radius_km),
                ]
            }
        },
        "sort": build_geo_sort(lat, lon),
        "size": size,
    }


def build_alerts_near_query(
    lat: float,
    lon: float,
    radius_km: float,
    active_only: bool = True,
    size: int = 20,
) -> dict:
    """Query para encontrar alertas cercanas."""
    filters = [build_geo_distance_filter(lat, lon, radius_km)]
    if active_only:
        filters.append({"term": {"is_active": True}})

    return {
        "query": {"bool": {"filter": filters}},
        "sort": [
            *build_geo_sort(lat, lon),
            {"urgency_score": {"order": "desc"}},
        ],
        "size": size,
    }
