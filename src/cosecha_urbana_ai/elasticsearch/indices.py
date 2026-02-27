"""Definición de mappings e índices de Elasticsearch."""

DONORS_MAPPING: dict = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "business_type": {"type": "keyword"},
            "contact_name": {"type": "keyword"},
            "contact_phone": {"type": "keyword"},
            "contact_email": {"type": "keyword"},
            "location": {"type": "geo_point"},
            "address": {"type": "text"},
            "city": {"type": "keyword"},
            "state": {"type": "keyword"},
            "typical_food_categories": {"type": "keyword"},
            "operating_hours": {
                "properties": {
                    "open": {"type": "keyword"},
                    "close": {"type": "keyword"},
                    "days": {"type": "keyword"},
                }
            },
            "has_refrigeration": {"type": "boolean"},
            "average_kg_per_donation": {"type": "float"},
            "is_active": {"type": "boolean"},
            "is_verified": {"type": "boolean"},
            "total_donations": {"type": "integer"},
            "total_kg_donated": {"type": "float"},
            "registered_at": {"type": "date"},
            "notes": {"type": "text"},
            "description_vector": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "similarity": "cosine",
            },
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
}

RECIPIENTS_MAPPING: dict = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "organization_type": {"type": "keyword"},
            "contact_name": {"type": "keyword"},
            "contact_phone": {"type": "keyword"},
            "contact_email": {"type": "keyword"},
            "location": {"type": "geo_point"},
            "address": {"type": "text"},
            "city": {"type": "keyword"},
            "state": {"type": "keyword"},
            "beneficiaries_count": {"type": "integer"},
            "accepted_food_categories": {"type": "keyword"},
            "dietary_restrictions": {"type": "keyword"},
            "storage_capacity": {
                "properties": {
                    "refrigerated_kg": {"type": "float"},
                    "frozen_kg": {"type": "float"},
                    "dry_kg": {"type": "float"},
                }
            },
            "receiving_hours_start": {"type": "keyword"},
            "receiving_hours_end": {"type": "keyword"},
            "available_days": {"type": "keyword"},
            "is_active": {"type": "boolean"},
            "is_verified": {"type": "boolean"},
            "current_need_level": {"type": "keyword"},
            "total_donations_received": {"type": "integer"},
            "total_kg_received": {"type": "float"},
            "needs_description": {"type": "text"},
            "needs_vector": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "similarity": "cosine",
            },
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
}

FOOD_ALERTS_MAPPING: dict = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "donor_id": {"type": "keyword"},
            "donor_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "food_category": {"type": "keyword"},
            "description": {"type": "text"},
            "quantity_kg": {"type": "float"},
            "expiry_datetime": {"type": "date"},
            "alert_created_at": {"type": "date"},
            "location": {"type": "geo_point"},
            "address": {"type": "text"},
            "urgency_level": {"type": "keyword"},
            "is_active": {"type": "boolean"},
            "matched_recipient_id": {"type": "keyword"},
            "special_requirements": {"type": "keyword"},
            "contact_phone": {"type": "keyword"},
            "hours_until_expiry": {"type": "float"},
            "urgency_score": {"type": "float"},
            "@timestamp": {"type": "date"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
}

DONATIONS_HISTORY_MAPPING: dict = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "alert_id": {"type": "keyword"},
            "donor_id": {"type": "keyword"},
            "donor_name": {"type": "keyword"},
            "recipient_id": {"type": "keyword"},
            "recipient_name": {"type": "keyword"},
            "food_category": {"type": "keyword"},
            "quantity_kg": {"type": "float"},
            "distance_km": {"type": "float"},
            "urgency_level": {"type": "keyword"},
            "status": {"type": "keyword"},
            "coordination_time_minutes": {"type": "float"},
            "pickup_location": {"type": "geo_point"},
            "delivery_location": {"type": "geo_point"},
            "created_at": {"type": "date"},
            "completed_at": {"type": "date"},
            "beneficiaries_served": {"type": "integer"},
            "agent_reasoning": {"type": "text"},
            "match_score": {"type": "float"},
            "@timestamp": {"type": "date"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
}

# Diccionario para setup automático - nombre_índice: mapping
ALL_INDICES: dict[str, dict] = {
    "cosecha_urbana_donors": DONORS_MAPPING,
    "cosecha_urbana_recipients": RECIPIENTS_MAPPING,
    "cosecha_urbana_food_alerts": FOOD_ALERTS_MAPPING,
    "cosecha_urbana_donations_history": DONATIONS_HISTORY_MAPPING,
}
