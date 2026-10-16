"""Validation and edge case tests for zero yield, zero revenue, invalid quantities, and negative costs."""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.calculator.engine import calculate_batch
from app.calculator.exceptions import NegativeValueValidationError, ZeroYieldError
from app.calculator.models import (
    BatchCostingInput,
    BatchYieldInput,
    IngredientInput,
)


def test_zero_sellable_yield_rejected():
    """Zero sellable quantity must raise ZeroYieldError."""
    with pytest.raises(ZeroYieldError):
        BatchYieldInput(sellable_quantity=Decimal("0"))

    with pytest.raises(ZeroYieldError):
        BatchYieldInput(gross_quantity=Decimal("50"), scrap_quantity=Decimal("50"))


def test_scrap_exceeding_gross_rejected():
    """Scrap quantity larger than gross output must raise NegativeValueValidationError."""
    with pytest.raises(NegativeValueValidationError):
        BatchYieldInput(gross_quantity=Decimal("20"), scrap_quantity=Decimal("25"))


def test_zero_selling_price_projections():
    """Zero selling price (free samples or donation) must not divide by zero or report false margins."""
    batch = BatchCostingInput(
        batch_name="Charity Feast",
        ingredients=[
            IngredientInput(
                name="Rice",
                recipe_quantity=Decimal("1"),
                recipe_unit="kg",
                purchase_price=Decimal("100.00"),
            )
        ],
        batch_yield=BatchYieldInput(sellable_quantity=Decimal("10")),
        planned_selling_price=Decimal("0.00"),
    )

    res = calculate_batch(batch)
    assert res.projected_revenue == Decimal("0.00")
    assert res.projected_profit == Decimal("-100.00")
    # Margin must be None because revenue is 0
    assert res.profit_margin_pct is None
    # Markup is -100%
    assert res.markup_pct == Decimal("-100.00")
    # Break-even units cannot be calculated at ₹0 price
    assert res.break_even_units_to_sell is None


def test_negative_costs_rejected_by_pydantic():
    """Negative money values must be blocked at validation."""
    with pytest.raises(ValidationError):
        IngredientInput(
            name="Sugar",
            recipe_quantity=Decimal("1"),
            recipe_unit="kg",
            purchase_price=Decimal("-50.00"),
        )

    with pytest.raises(ValidationError):
        BatchCostingInput(
            batch_name="Invalid Cost Batch",
            ingredients=[
                IngredientInput(
                    name="Flour",
                    recipe_quantity=Decimal("1"),
                    recipe_unit="kg",
                    purchase_price=Decimal("50.00"),
                )
            ],
            packaging_cost=Decimal("-10.00"),
            batch_yield=BatchYieldInput(sellable_quantity=Decimal("1")),
        )


def test_empty_ingredients_rejected():
    """Batch with no ingredients must be rejected."""
    with pytest.raises(ValidationError):
        BatchCostingInput(
            batch_name="Empty Batch",
            ingredients=[],
            batch_yield=BatchYieldInput(sellable_quantity=Decimal("1")),
        )


def test_actual_units_sold_exceeding_sellable_rejected():
    """Cannot record selling more units than produced in the batch."""
    with pytest.raises(NegativeValueValidationError):
        BatchCostingInput(
            batch_name="Over-sold Batch",
            ingredients=[
                IngredientInput(
                    name="Flour",
                    recipe_quantity=Decimal("1"),
                    recipe_unit="kg",
                    purchase_price=Decimal("50.00"),
                )
            ],
            batch_yield=BatchYieldInput(sellable_quantity=Decimal("50")),
            actual_units_sold=Decimal("60"),
        )


def test_empty_yield_input_raises_zero_yield():
    """BatchYieldInput with no quantity specified raises ZeroYieldError."""
    with pytest.raises(ZeroYieldError) as exc:
        BatchYieldInput()
    assert "Either sellable_quantity or gross_quantity (>0) must be specified." in str(exc.value)


def test_are_units_compatible_with_unknown_unit():
    """are_units_compatible returns False gracefully when given unknown units."""
    from app.calculator.units import are_units_compatible
    assert are_units_compatible("mystery_unit", "kg") is False
    assert are_units_compatible("kg", "mystery_unit") is False


def test_convert_quantity_with_non_decimal_input():
    """convert_quantity coerces integer or string input to Decimal safely."""
    from app.calculator.units import convert_quantity
    assert convert_quantity(5, "kg", "g") == Decimal("5000")
    assert convert_quantity("250", "ml", "l") == Decimal("0.25")


def test_zero_total_batch_cost_handles_markup_gracefully():
    """When a batch has 0 total cost (e.g. gifted ingredients), markup is None instead of zero division."""
    batch = BatchCostingInput(
        batch_name="Donated Grains Batch",
        ingredients=[
            IngredientInput(
                name="Donated Wheat",
                recipe_quantity=Decimal("1"),
                recipe_unit="kg",
                purchase_price=Decimal("0.00"),
            )
        ],
        batch_yield=BatchYieldInput(sellable_quantity=Decimal("10")),
        planned_selling_price=Decimal("5.00"),
    )
    res = calculate_batch(batch)
    assert res.total_batch_cost == Decimal("0.00")
    assert res.markup_pct is None
    assert res.profit_margin_pct == Decimal("100.00")  # (50 - 0) / 50 * 100 = 100%


def test_engine_defensive_guards():
    """Verify engine-level defensive guards when inputs are constructed without Pydantic validation."""
    from app.calculator.exceptions import InvalidTargetMarginError

    # Test sellable_quantity <= 0 guard in engine
    unvalidated_batch = BatchCostingInput.model_construct(
        batch_name="Defensive Yield Test",
        ingredients=[],
        packaging_cost=Decimal("0"),
        labour_cost=Decimal("0"),
        fuel_cost=Decimal("0"),
        delivery_cost=Decimal("0"),
        other_expenses=Decimal("0"),
        direct_wastage_expense=Decimal("0"),
        batch_yield=BatchYieldInput.model_construct(sellable_quantity=Decimal("0"), unit_name="pkt"),
        planned_selling_price=None,
        target_margin_pct=None,
        actual_units_sold=None,
    )
    with pytest.raises(ZeroYieldError):
        calculate_batch(unvalidated_batch)

    # Test target_margin >= 100 guard in engine
    unvalidated_margin = BatchCostingInput.model_construct(
        batch_name="Defensive Margin Test",
        ingredients=[],
        packaging_cost=Decimal("0"),
        labour_cost=Decimal("0"),
        fuel_cost=Decimal("0"),
        delivery_cost=Decimal("0"),
        other_expenses=Decimal("0"),
        direct_wastage_expense=Decimal("0"),
        batch_yield=BatchYieldInput.model_construct(sellable_quantity=Decimal("10"), unit_name="pkt"),
        planned_selling_price=None,
        target_margin_pct=Decimal("150.00"),
        actual_units_sold=None,
    )
    with pytest.raises(InvalidTargetMarginError):
        calculate_batch(unvalidated_margin)


