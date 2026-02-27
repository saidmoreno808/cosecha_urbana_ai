"""Unit tests para los modelos Pydantic."""
import pytest
from datetime import datetime, timezone, timedelta

from src.cosecha_urbana_ai.models.food_alert import (
    FoodAlert,
    FoodCategory,
    GeoPoint,
    UrgencyLevel,
)
from src.cosecha_urbana_ai.models.recipient import Recipient, StorageCapacity


class TestFoodAlert:
    def test_valid_alert_creation(self):
        alert = FoodAlert(
            donor_id="test-donor",
            donor_name="Test Donor",
            food_category=FoodCategory.PREPARED,
            description="Test food description that is long enough",
            quantity_kg=10.0,
            expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=5),
            location=GeoPoint(lat=25.65, lon=-100.37),
            address="Test address Monterrey",
        )
        assert alert.donor_id == "test-donor"
        assert alert.quantity_kg == 10.0

    def test_expiry_in_past_raises_error(self):
        with pytest.raises(ValueError, match="Expiry datetime must be in the future"):
            FoodAlert(
                donor_id="test",
                donor_name="Test",
                food_category=FoodCategory.DRY_GOODS,
                description="Test description long enough",
                quantity_kg=5.0,
                expiry_datetime=datetime(2020, 1, 1, tzinfo=timezone.utc),
                location=GeoPoint(lat=25.65, lon=-100.37),
                address="Test address",
            )

    def test_urgency_critical_under_2h(self):
        alert = FoodAlert(
            donor_id="test",
            donor_name="Test",
            food_category=FoodCategory.PREPARED,
            description="Urgent food item description",
            quantity_kg=5.0,
            expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
            location=GeoPoint(lat=25.65, lon=-100.37),
            address="Test address",
        )
        assert alert.compute_urgency() == UrgencyLevel.CRITICAL

    def test_urgency_low_over_12h(self):
        alert = FoodAlert(
            donor_id="test",
            donor_name="Test",
            food_category=FoodCategory.DRY_GOODS,
            description="Low urgency food item description",
            quantity_kg=5.0,
            expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=24),
            location=GeoPoint(lat=25.65, lon=-100.37),
            address="Test address",
        )
        assert alert.compute_urgency() == UrgencyLevel.LOW

    def test_hours_until_expiry_calculation(self):
        hours = 6.0
        alert = FoodAlert(
            donor_id="test",
            donor_name="Test",
            food_category=FoodCategory.PRODUCE,
            description="Fresh produce description item",
            quantity_kg=5.0,
            expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=hours),
            location=GeoPoint(lat=25.65, lon=-100.37),
            address="Test address",
        )
        assert abs(alert.hours_until_expiry - hours) < 0.1

    def test_geopoint_validation_invalid_lat(self):
        with pytest.raises(Exception):
            GeoPoint(lat=91.0, lon=-100.37)

    def test_to_es_doc_has_location(self):
        alert = FoodAlert(
            donor_id="test",
            donor_name="Test",
            food_category=FoodCategory.BAKERY,
            description="Bakery items description is long",
            quantity_kg=5.0,
            expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=5),
            location=GeoPoint(lat=25.65, lon=-100.37),
            address="Test",
        )
        doc = alert.to_es_doc()
        assert "lat" in doc["location"]
        assert "lon" in doc["location"]
        assert "hours_until_expiry" in doc
        assert "@timestamp" in doc


class TestRecipient:
    def test_valid_recipient(self, sample_recipient):
        assert sample_recipient.beneficiaries_count == 120
        assert sample_recipient.current_need_level == "high"

    def test_storage_capacity_defaults(self):
        cap = StorageCapacity()
        assert cap.refrigerated_kg == 0.0
        assert cap.dry_kg == 0.0
