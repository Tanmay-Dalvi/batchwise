"""Scenario tests for target-margin pricing, markup contrasts, and sales realization."""

from decimal import Decimal
import pytest

from app.calculator.engine import calculate_batch
from app.calculator.exceptions import InvalidTargetMarginError
from app.calculator.models import (
    BatchCostingInput,
    BatchYieldInput,
    IngredientInput,
)


def test_target_margin_pricing_and_markup_distinction():
    """
    Demonstrate that a 20% target margin requires selling price of ₹25.00 when cost is ₹20.00,
    and corresponds to a 25% markup on cost.
    """
    batch = BatchCostingInput(
        batch_name="Standard Tiffin Meal",
        ingredients=[
            IngredientInput(
                name="Rice, Dal, Veggies",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("18.00"),
            )
        ],
        packaging_cost=Decimal("2.00"),  # Total unit cost = ₹20.00
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("1"),
            unit_name="tiffin",
        ),
        target_margin_pct=Decimal("20.00"),
    )

    res = calculate_batch(batch)

    assert res.cost_per_sellable_unit == Decimal("20.00")
    # P_target = 20 / (1 - 0.20) = 20 / 0.80 = 25.00
    assert res.target_margin_selling_price == Decimal("25.00")
    assert res.target_margin_profit_per_unit == Decimal("5.00")
    # Markup = 5 / 20 = 25.00%
    assert res.target_margin_markup_pct == Decimal("25.00")

    # If the user instead set price with 20% markup, price would be ₹24.00, yielding only 16.67% margin
    sub_batch = batch.model_copy(update={"planned_selling_price": Decimal("24.00")})
    sub_res = calculate_batch(sub_batch)
    assert sub_res.profit_margin_pct == Decimal("16.67")  # 4 / 24 = 16.666...%


def test_target_margin_high_margins():
    """Verify target margin pricing at 50% margin (100% markup)."""
    batch = BatchCostingInput(
        batch_name="Artisanal Brownies",
        ingredients=[
            IngredientInput(
                name="Chocolate & Walnuts",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("50.00"),
            )
        ],
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("1"),
            unit_name="box",
        ),
        target_margin_pct=Decimal("50.00"),
    )

    res = calculate_batch(batch)
    # 50 / (1 - 0.50) = ₹100.00
    assert res.target_margin_selling_price == Decimal("100.00")
    assert res.target_margin_profit_per_unit == Decimal("50.00")
    assert res.target_margin_markup_pct == Decimal("100.00")


def test_target_margin_zero_margin():
    """Target margin of 0% yields exactly the break-even unit cost."""
    batch = BatchCostingInput(
        batch_name="Cost-Price Community Kitchen Batch",
        ingredients=[
            IngredientInput(
                name="Grains",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("30.00"),
            )
        ],
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("1"),
            unit_name="meal",
        ),
        target_margin_pct=Decimal("0.00"),
    )

    res = calculate_batch(batch)
    assert res.target_margin_selling_price == Decimal("30.00")
    assert res.target_margin_profit_per_unit == Decimal("0.00")
    assert res.target_margin_markup_pct == Decimal("0.00")


def test_invalid_target_margin_values():
    """Target margin >= 100% or < 0% must be rejected."""
    # 100% margin requires infinite price
    with pytest.raises(InvalidTargetMarginError):
        BatchCostingInput(
            batch_name="Impossible Batch",
            ingredients=[
                IngredientInput(
                    name="Flour",
                    recipe_quantity=Decimal("1"),
                    recipe_unit="kg",
                    purchase_price=Decimal("50.00"),
                )
            ],
            batch_yield=BatchYieldInput(sellable_quantity=Decimal("1")),
            target_margin_pct=Decimal("100.00"),
        )

    # Negative margin
    with pytest.raises(InvalidTargetMarginError):
        BatchCostingInput(
            batch_name="Negative Margin Batch",
            ingredients=[
                IngredientInput(
                    name="Flour",
                    recipe_quantity=Decimal("1"),
                    recipe_unit="kg",
                    purchase_price=Decimal("50.00"),
                )
            ],
            batch_yield=BatchYieldInput(sellable_quantity=Decimal("1")),
            target_margin_pct=Decimal("-5.00"),
        )


def test_realized_sales_cash_flow_tracking():
    """
    Test partial batch sales accounting:
    Batch of 100 snack boxes costing ₹1,000 total (unit cost ₹10).
    Sold at ₹20 per box. Break-even volume is 50 boxes.
    """
    # 1. Partial sale below break-even (30 boxes sold)
    batch_under = BatchCostingInput(
        batch_name="Mathri Snack Boxes",
        ingredients=[
            IngredientInput(
                name="Flour, Spices, Ghee",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("1000.00"),
            )
        ],
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("100"),
            unit_name="boxes",
        ),
        planned_selling_price=Decimal("20.00"),
        actual_units_sold=Decimal("30"),
    )

    res_under = calculate_batch(batch_under)
    assert res_under.actual_units_sold == Decimal("30")
    assert res_under.unsold_units == Decimal("70")
    assert res_under.realized_revenue == Decimal("600.00")  # 30 * 20
    assert res_under.cogs_sold_units == Decimal("300.00")   # 30 * 10
    assert res_under.realized_gross_profit == Decimal("300.00")
    # Net cashflow is negative (600 collected - 1000 spent = -400)
    assert res_under.net_cashflow == Decimal("-400.00")
    # Unsold inventory cost value = 70 * 10 = ₹700
    assert res_under.unsold_inventory_cost_value == Decimal("700.00")
    # Reconciliation: Cashflow (-400) + Inventory (700) = Realized Gross Profit (300)
    assert res_under.net_cashflow + res_under.unsold_inventory_cost_value == res_under.realized_gross_profit

    # 2. Sale above break-even (75 boxes sold)
    batch_over = batch_under.model_copy(update={"actual_units_sold": Decimal("75")})
    res_over = calculate_batch(batch_over)
    assert res_over.unsold_units == Decimal("25")
    assert res_over.realized_revenue == Decimal("1500.00")  # 75 * 20
    assert res_over.cogs_sold_units == Decimal("750.00")    # 75 * 10
    assert res_over.realized_gross_profit == Decimal("750.00")
    # Net cashflow is positive (1500 - 1000 = +500)
    assert res_over.net_cashflow == Decimal("500.00")
    assert res_over.unsold_inventory_cost_value == Decimal("250.00")

