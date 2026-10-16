"""Tests for the calculation API endpoint verifying pure deterministic execution and error formats."""

from decimal import Decimal
from fastapi import status


def test_calculate_endpoint_success(client, canonical_besan_payload):
    """POST /api/v1/calculate calculates correct costs and returns serialized Decimal outputs."""
    response = client.post("/api/v1/calculate", json=canonical_besan_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Exact cost verification
    assert data["batch_name"] == "Diwali Besan Sev Batch"
    assert data["total_ingredients_cost"] == "780.00"
    assert data["packaging_cost"] == "80.00"
    assert data["total_batch_cost"] == "860.00"
    assert data["sellable_quantity"] == "75"
    assert data["unit_name"] == "packets"
    assert data["cost_per_sellable_unit"] == "11.47"
    assert data["break_even_price_per_unit"] == "11.47"

    # Pricing & Projections at ₹25.00
    assert data["planned_selling_price"] == "25.00"
    assert data["projected_revenue"] == "1875.00"
    assert data["projected_profit"] == "1015.00"
    assert data["profit_margin_pct"] == "54.13"
    assert data["markup_pct"] == "118.02"
    assert data["break_even_units_to_sell"] == "35"

    # Target Margin (30%)
    # P_target = 11.46666... / (1 - 0.30) = 16.3809... -> 16.38
    assert data["target_margin_selling_price"] == "16.38"
    assert data["target_margin_markup_pct"] == "42.86"

    # Decimal string serialization check: types must be string to prevent binary float corruption
    assert isinstance(data["total_batch_cost"], str)
    assert isinstance(data["cost_per_sellable_unit"], str)

    # Audit trail validation
    assert len(data["audit_trail"]) >= 4
    step_names = [s["step_name"] for s in data["audit_trail"]]
    assert "TOTAL_BATCH_COST" in step_names
    assert "UNIT_COST_AND_BREAK_EVEN" in step_names


def test_calculate_zero_yield_error(client, canonical_besan_payload):
    """Zero sellable quantity returns HTTP 422 with structured ZeroYieldError."""
    payload = dict(canonical_besan_payload)
    payload["batch_yield"] = {"sellable_quantity": "0"}

    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


def test_calculate_incompatible_units_error(client, canonical_besan_payload):
    """Incompatible unit conversion (e.g. kg to ml) returns HTTP 422 with IncompatibleUnitDimensionError."""
    payload = dict(canonical_besan_payload)
    payload["ingredients"] = [
        {
            "name": "Besan",
            "recipe_quantity": "500",
            "recipe_unit": "ml",  # Volume!
            "purchase_quantity": "1",
            "purchase_unit": "kg",  # Mass!
            "purchase_price": "100.00",
        }
    ]

    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["detail"]["error_type"] == "IncompatibleUnitDimensionError"
    assert "Cannot convert 'ml' (VOLUME) to 'kg' (MASS)" in data["detail"]["message"]


def test_calculate_invalid_target_margin(client, canonical_besan_payload):
    """Target margin >= 100% returns HTTP 422 with InvalidTargetMarginError."""
    payload = dict(canonical_besan_payload)
    payload["target_margin_pct"] = "105.00"

    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


def test_calculate_negative_cost_rejected(client, canonical_besan_payload):
    """Negative money values fail request validation."""
    payload = dict(canonical_besan_payload)
    payload["packaging_cost"] = "-50.00"

    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_calculate_empty_ingredients_rejected(client, canonical_besan_payload):
    """Empty ingredients list fails validation."""
    payload = dict(canonical_besan_payload)
    payload["ingredients"] = []

    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_calculate_generic_batchwise_error(client, canonical_besan_payload, monkeypatch):
    """Verify generic BatchwiseError results in HTTP 400 Bad Request."""
    from app.calculator.exceptions import BatchwiseError
    import app.api.v1.calculate as calc_module

    def mock_calculate(data):
        raise BatchwiseError("Generic domain calculation failure")

    monkeypatch.setattr(calc_module, "calculate_batch", mock_calculate)
    response = client.post("/api/v1/calculate", json=canonical_besan_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error_type"] == "BatchwiseError"
    assert "Generic domain calculation failure" in data["detail"]["message"]

