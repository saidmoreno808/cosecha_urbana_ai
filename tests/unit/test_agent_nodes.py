"""Unit tests para los nodos del agente LangGraph."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from src.cosecha_urbana_ai.models.food_alert import FoodAlert, FoodCategory, GeoPoint


class TestAnalyzeNode:
    @pytest.mark.asyncio
    async def test_critical_urgency_prepared_food(self, sample_food_alert, base_agent_state):
        """Comida preparada con < 2h debe tener urgency_score alto."""
        from src.cosecha_urbana_ai.agent.nodes import analyze_node

        state = {
            **base_agent_state,
            "alert": FoodAlert(
                **{
                    **sample_food_alert.model_dump(exclude={"id", "expiry_datetime"}),
                    "id": sample_food_alert.id,
                    "expiry_datetime": datetime.now(timezone.utc) + timedelta(hours=1),
                    "food_category": FoodCategory.PREPARED,
                }
            ),
        }

        with patch("src.cosecha_urbana_ai.agent.nodes.analyze_node.get_es_client") as mock_es:
            mock_client = AsyncMock()
            mock_client.esql = AsyncMock()
            mock_client.esql.query = AsyncMock(return_value={"columns": [], "rows": [[1, 10.0]]})
            mock_es.return_value = mock_client

            result = await analyze_node.run(state)

        assert result["urgency_score"] >= 0.8, "1h prepared food should have high urgency"
        assert "analyze_node:completed" in result["steps_taken"]
        assert result["analysis_reasoning"] != ""

    @pytest.mark.asyncio
    async def test_low_urgency_dry_goods(self, sample_food_alert, base_agent_state):
        """Granos secos con > 24h deben tener urgency_score bajo."""
        from src.cosecha_urbana_ai.agent.nodes import analyze_node

        state = {
            **base_agent_state,
            "alert": FoodAlert(
                **{
                    **sample_food_alert.model_dump(exclude={"id", "expiry_datetime", "food_category"}),
                    "id": sample_food_alert.id,
                    "expiry_datetime": datetime.now(timezone.utc) + timedelta(hours=48),
                    "food_category": FoodCategory.DRY_GOODS,
                }
            ),
        }

        with patch("src.cosecha_urbana_ai.agent.nodes.analyze_node.get_es_client") as mock_es:
            mock_client = AsyncMock()
            mock_client.esql = AsyncMock()
            mock_client.esql.query = AsyncMock(return_value={"columns": [], "rows": []})
            mock_es.return_value = mock_client

            result = await analyze_node.run(state)

        assert result["urgency_score"] < 0.3, "48h dry goods should be low urgency"

    @pytest.mark.asyncio
    async def test_analyze_records_steps(self, base_agent_state):
        """El nodo debe registrar sus pasos en steps_taken."""
        from src.cosecha_urbana_ai.agent.nodes import analyze_node

        with patch("src.cosecha_urbana_ai.agent.nodes.analyze_node.get_es_client") as mock_es:
            mock_client = AsyncMock()
            mock_client.esql = AsyncMock()
            mock_client.esql.query = AsyncMock(return_value={"columns": [], "rows": []})
            mock_es.return_value = mock_client

            result = await analyze_node.run(base_agent_state)

        assert "analyze_node:started" in result["steps_taken"]
        assert "analyze_node:completed" in result["steps_taken"]


class TestValidateNode:
    @pytest.mark.asyncio
    async def test_validate_success(self, base_agent_state, sample_recipient):
        """Validación exitosa cuando hay receptor y ejecución completada."""
        from src.cosecha_urbana_ai.agent.nodes import validate_node

        state = {
            **base_agent_state,
            "selected_recipient": sample_recipient,
            "execution_status": "completed",
            "match_score": 0.85,
            "notifications_sent": ["donor:001", "recipient:001"],
        }

        result = await validate_node.run(state)

        assert result["validation_passed"] is True
        assert "completed_at" in result
        assert result["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_validate_fails_without_recipient(self, base_agent_state):
        """Validación falla si no hay receptor."""
        from src.cosecha_urbana_ai.agent.nodes import validate_node

        state = {
            **base_agent_state,
            "selected_recipient": None,
            "execution_status": "",
        }

        result = await validate_node.run(state)
        assert result["validation_passed"] is False

    @pytest.mark.asyncio
    async def test_validate_records_steps(self, base_agent_state):
        """El nodo debe registrar sus pasos."""
        from src.cosecha_urbana_ai.agent.nodes import validate_node

        result = await validate_node.run(base_agent_state)

        assert "validate_node:started" in result["steps_taken"]
        assert "validate_node:completed" in result["steps_taken"]
