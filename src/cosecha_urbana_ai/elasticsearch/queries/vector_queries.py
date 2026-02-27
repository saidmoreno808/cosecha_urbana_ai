"""Queries de búsqueda vectorial (kNN / semantic search)."""


def build_knn_recipients_query(
    query_vector: list[float],
    k: int = 5,
    num_candidates: int = 50,
    filter_food_category: str | None = None,
) -> dict:
    """
    Búsqueda kNN semántica sobre needs_vector de receptores.

    Combina vector similarity con filtros de negocio.
    """
    knn_query: dict = {
        "field": "needs_vector",
        "query_vector": query_vector,
        "k": k,
        "num_candidates": num_candidates,
    }

    if filter_food_category:
        knn_query["filter"] = {
            "bool": {
                "filter": [
                    {"term": {"is_active": True}},
                    {"term": {"accepted_food_categories": filter_food_category}},
                ]
            }
        }
    else:
        knn_query["filter"] = {"term": {"is_active": True}}

    return {"knn": knn_query, "_source": True}


def build_hybrid_recipient_query(
    query_vector: list[float],
    lat: float,
    lon: float,
    radius_km: float,
    food_category: str,
    k: int = 5,
) -> dict:
    """
    Query híbrida: kNN vectorial + filtro geográfico + compatibilidad.
    Combina semántica (qué necesita) con proximidad (dónde está).
    """
    return {
        "knn": {
            "field": "needs_vector",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": 100,
            "filter": {
                "bool": {
                    "filter": [
                        {"term": {"is_active": True}},
                        {"term": {"accepted_food_categories": food_category}},
                        {
                            "geo_distance": {
                                "distance": f"{radius_km}km",
                                "location": {"lat": lat, "lon": lon},
                            }
                        },
                    ]
                }
            },
        },
        "_source": True,
    }
