"""Fixtures compartidos para todos los tests."""
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest

from src.cosecha_urbana_ai.models.food_alert import FoodAlert, FoodCategory, GeoPoint, UrgencyLevel
from src.cosecha_urbana_ai.models.recipient import Recipient, StorageCapacity
from src.cosecha_urbana_ai.models.donor import Donor, OperatingHours


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_food_alert() -> FoodAlert:
    return FoodAlert(
        id="alert-test-001",
        donor_id="donor-001",
        donor_name="Plaza Fiesta San Agustín — Food Court",
        food_category=FoodCategory.PREPARED,
        description="Arroz con pollo preparado, 50 porciones individuales",
        quantity_kg=15.0,
        expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=3),
        location=GeoPoint(lat=25.6531, lon=-100.3679),
        address="Av. Gómez Morín 444, San Agustín, Monterrey",
        special_requirements=["refrigeration"],
        urgency_level=UrgencyLevel.HIGH,
        contact_phone="+528112000001",
    )


@pytest.fixture
def sample_recipient() -> Recipient:
    return Recipient(
        id="recipient-test-001",
        name="Casa del Migrante San Pedro",
        organization_type="migrant_house",
        contact_name="Hermana María García",
        contact_phone="+528112100001",
        contact_email="contacto@casamigrante.org",
        location=GeoPoint(lat=25.6511, lon=-100.3589),
        address="Calle Padre Mier 100, Centro, Monterrey",
        beneficiaries_count=120,
        accepted_food_categories=[FoodCategory.PREPARED, FoodCategory.DAIRY],
        storage_capacity=StorageCapacity(refrigerated_kg=50.0, dry_kg=200.0),
        current_need_level="high",
        distance_km=1.5,
    )


@pytest.fixture
def mock_es_client():
    """Mock del cliente Elasticsearch para unit tests."""
    client = AsyncMock()
    client.info = AsyncMock(return_value={"cluster_name": "test", "version": {"number": "8.13.0"}})
    client.search = AsyncMock(
        return_value={
            "hits": {
                "hits": [],
                "total": {"value": 0},
            }
        }
    )
    client.index = AsyncMock(return_value={"_id": "test-id-123", "result": "created"})
    client.get = AsyncMock(
        side_effect=Exception("Not found")
    )
    client.update = AsyncMock(return_value={"result": "updated"})
    client.count = AsyncMock(return_value={"count": 0})
    client.esql = AsyncMock()
    client.esql.query = AsyncMock(return_value={"columns": [], "rows": []})
    client.indices = AsyncMock()
    client.indices.exists = AsyncMock(return_value=False)
    client.indices.create = AsyncMock(return_value={"acknowledged": True})
    return client


@pytest.fixture
def base_agent_state(sample_food_alert) -> dict:
    return {
        "alert_id": "alert-test-001",
        "alert": sample_food_alert,
        "urgency_score": 0.0,
        "priority_rank": 0,
        "analysis_reasoning": "",
        "candidate_recipients": [],
        "selected_recipient": None,
        "match_score": 0.0,
        "match_reasoning": "",
        "distance_km": 0.0,
        "route": None,
        "notifications_sent": [],
        "execution_status": "pending",
        "validation_passed": False,
        "validation_notes": "",
        "steps_taken": [],
        "errors": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "messages": [],
    }
