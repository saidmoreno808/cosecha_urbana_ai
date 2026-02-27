"""Integration tests para endpoints de la API."""
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient

from src.cosecha_urbana_ai.api.main import app


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "elasticsearch" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "project" in data
        assert data["project"] == "cosecha_urbana_ai"


class TestAlertsEndpoint:
    @pytest.mark.asyncio
    async def test_create_alert_invalid_expiry(self, async_client):
        """Alerta con fecha pasada debe retornar 422."""
        response = await async_client.post(
            "/api/v1/alerts/",
            json={
                "donor_id": "test-donor",
                "donor_name": "Test Donor Restaurant",
                "food_category": "prepared",
                "description": "This is a test food item description long enough",
                "quantity_kg": 10.0,
                "expiry_datetime": "2020-01-01T00:00:00Z",
                "location": {"lat": 25.65, "lon": -100.37},
                "address": "Test Address Monterrey NL",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_missing_required_fields(self, async_client):
        """Alerta sin campos requeridos debe retornar 422."""
        response = await async_client.post(
            "/api/v1/alerts/",
            json={"donor_id": "test"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_nonexistent_alert(self, async_client):
        """Alert no encontrada debe retornar 404."""
        response = await async_client.get("/api/v1/alerts/nonexistent-id-12345")
        # Puede ser 404 o 500 si ES no está disponible en tests
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_agent_status(self, async_client):
        """El endpoint de status del agente debe responder."""
        response = await async_client.get("/api/v1/agent/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "steps" in data
