"""Audit trace tests verifying complete transparency and step-by-step math explanations."""

from decimal import Decimal

from app.calculator.engine import calculate_batch
from app.calculator.models import (
    BatchCostingInput,
    BatchYieldInput,
    IngredientInput,
)


def test_audit_trail_completeness_and_transparency():
    """Verify that every calculation generates transparent, human-readable audit steps."""
    batch = BatchCostingInput(
        batch_name="Gulab Jamun Audit Test",
        ingredients=[
            IngredientInput(
                name="Mawa",
                recipe_quantity=Decimal("500"),
                recipe_unit="g",
                purchase_quantity=Decimal("1"),
                purchase_unit="kg",
                purchase_price=Decimal("400.00"),
            ),
            IngredientInput(
                name="Sugar",
                recipe_quantity=Decimal("1"),
                recipe_unit="kg",
                purchase_price=Decimal("45.00"),
            ),
        ],
        packaging_cost=Decimal("30.00"),
        fuel_cost=Decimal("25.00"),
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("50"),
            unit_name="boxes",
        ),
        planned_selling_price=Decimal("15.00"),
        target_margin_pct=Decimal("30.00"),
        actual_units_sold=Decimal("35"),
    )

    res = calculate_batch(batch)

    # Collect step names
    step_names = [step.step_name for step in res.audit_trail]
    assert "INGREDIENT_COST:Mawa" in step_names
    assert "INGREDIENT_COST:Sugar" in step_names
    assert "TOTAL_BATCH_COST" in step_names
    assert "UNIT_COST_AND_BREAK_EVEN" in step_names
    assert "PRICING_AND_MARGIN_PROJECTION" in step_names
    assert "TARGET_MARGIN_RECOMMENDATION" in step_names
    assert "REALIZED_SALES_PERFORMANCE" in step_names

    # Inspect individual audit steps for completeness
    for step in res.audit_trail:
        assert step.step_name != ""
        assert step.formula != ""
        assert isinstance(step.inputs, dict)
        assert len(step.inputs) > 0
        assert step.result != ""
        assert step.explanation != ""
        # Values must be stringified without binary float representations
        for k, v in step.inputs.items():
            assert not isinstance(v, float)
            assert isinstance(v, str)

    # Check specific explanation content
    mawa_step = next(s for s in res.audit_trail if s.step_name == "INGREDIENT_COST:Mawa")
    assert "Used 500 g" in mawa_step.explanation
    assert "₹200.00" in mawa_step.explanation

