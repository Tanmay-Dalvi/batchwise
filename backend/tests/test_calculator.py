"""Core financial calculator test suite covering deterministic arithmetic, rounding, and wastage."""

from decimal import Decimal
import pytest

from app.calculator.engine import (
    calculate_batch,
    calculate_ingredient_cost,
    round_currency,
    round_percent,
)
from app.calculator.models import (
    BatchCostingInput,
    BatchYieldInput,
    IngredientInput,
)


def test_canonical_besan_batch_costing():
    """
    Test the canonical prompt example:
    '5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, sold each for 25.'
    """
    batch = BatchCostingInput(
        batch_name="Diwali Besan Sev Batch",
        ingredients=[
            IngredientInput(
                name="Besan (Gram Flour)",
                recipe_quantity=Decimal("5"),
                recipe_unit="kg",
                purchase_quantity=Decimal("5"),
                purchase_unit="kg",
                purchase_price=Decimal("600.00"),
            ),
            IngredientInput(
                name="Cooking Oil",
                recipe_quantity=Decimal("1"),
                recipe_unit="l",
                purchase_quantity=Decimal("1"),
                purchase_unit="l",
                purchase_price=Decimal("180.00"),
            ),
        ],
        packaging_cost=Decimal("80.00"),
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("75"),
            unit_name="packets",
        ),
        planned_selling_price=Decimal("25.00"),
    )

    result = calculate_batch(batch)

    # Ingredients & Total Cost
    assert result.total_ingredients_cost == Decimal("780.00")
    assert result.packaging_cost == Decimal("80.00")
    assert result.total_overheads == Decimal("80.00")
    assert result.total_batch_cost == Decimal("860.00")

    # Yield & Unit Cost (860 / 75 = 11.466666...)
    assert result.sellable_quantity == Decimal("75")
    assert result.cost_per_sellable_unit == Decimal("11.47")
    assert result.break_even_price_per_unit == Decimal("11.47")

    # Revenue & Profit Projections (at ₹25.00)
    assert result.projected_revenue == Decimal("1875.00")  # 75 * 25
    assert result.projected_profit == Decimal("1015.00")   # 1875 - 860
    assert result.profit_per_unit == Decimal("13.53")     # 25.00 - 11.47 (rounded exact: 13.5333...)

    # Margin vs Markup
    # Margin = 1015 / 1875 * 100 = 54.1333...% -> 54.13%
    assert result.profit_margin_pct == Decimal("54.13")
    # Markup = 1015 / 860 * 100 = 118.0232...% -> 118.02%
    assert result.markup_pct == Decimal("118.02")

    # Break-even units to sell: ceil(860 / 25) = 35 units
    assert result.break_even_units_to_sell == Decimal("35")
    # Verification: 35 packets * ₹25 = ₹875 (> ₹860 cost), whereas 34 * ₹25 = ₹850 (< ₹860 cost)
    assert (Decimal("35") * Decimal("25.00")) >= Decimal("860.00")
    assert (Decimal("34") * Decimal("25.00")) < Decimal("860.00")


def test_ingredient_unit_conversions_in_batch():
    """Verify purchasing in bulk with fractional recipe usage computes exact cost."""
    # Bought 10 kg sugar for ₹450, recipe uses 750 g
    sugar = IngredientInput(
        name="Sugar",
        recipe_quantity=Decimal("750"),
        recipe_unit="g",
        purchase_quantity=Decimal("10"),
        purchase_unit="kg",
        purchase_price=Decimal("450.00"),
    )
    sugar_res = calculate_ingredient_cost(sugar)
    # 750 g is 0.75 kg -> (0.75 / 10) * 450 = ₹33.75
    assert sugar_res.cost == Decimal("33.75")
    assert sugar_res.exact_cost == Decimal("33.75")

    # Bought 2 l pure ghee for ₹1400, recipe uses 350 ml
    ghee = IngredientInput(
        name="Pure Ghee",
        recipe_quantity=Decimal("350"),
        recipe_unit="ml",
        purchase_quantity=Decimal("2"),
        purchase_unit="l",
        purchase_price=Decimal("1400.00"),
    )
    ghee_res = calculate_ingredient_cost(ghee)
    # (0.35 / 2) * 1400 = 0.175 * 1400 = ₹245.00
    assert ghee_res.cost == Decimal("245.00")
    assert ghee_res.exact_cost == Decimal("245.00")

    # Bought 3 dozen eggs for ₹216, recipe uses 6 units
    eggs = IngredientInput(
        name="Eggs",
        recipe_quantity=Decimal("6"),
        recipe_unit="unit",
        purchase_quantity=Decimal("3"),
        purchase_unit="dozen",
        purchase_price=Decimal("216.00"),
    )
    eggs_res = calculate_ingredient_cost(eggs)
    # 3 dozen = 36 units. 6 / 36 * 216 = ₹36.00
    assert eggs_res.cost == Decimal("36.00")
    assert eggs_res.exact_cost == Decimal("36.00")


def test_wastage_no_double_counting():
    """
    Ensure wastage is not double-counted when it is reflected in sellable yield.
    If 100 cookies cost ₹1,000, and 10 cookies are scrapped, 90 sellable cookies cost ₹11.11 each.
    The batch cost must remain ₹1,000, NOT ₹1,100.
    """
    batch = BatchCostingInput(
        batch_name="Chocolate Chip Cookies",
        ingredients=[
            IngredientInput(
                name="Flour, Butter, Choc Chips",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("900.00"),
            ),
        ],
        packaging_cost=Decimal("50.00"),
        fuel_cost=Decimal("50.00"),
        # Total production outlay = ₹1000.00
        batch_yield=BatchYieldInput(
            gross_quantity=Decimal("100"),
            scrap_quantity=Decimal("10"),
            unit_name="cookies",
        ),
        planned_selling_price=Decimal("20.00"),
    )

    res = calculate_batch(batch)

    # 1. Total batch cost must be strictly the actual cash spent: ₹1000.00
    assert res.total_batch_cost == Decimal("1000.00")
    # 2. Sellable quantity is 90
    assert res.sellable_quantity == Decimal("90")
    assert res.gross_quantity == Decimal("100")
    assert res.scrap_quantity == Decimal("10")
    # 3. Unit cost is 1000 / 90 = 11.1111... -> ₹11.11
    assert res.cost_per_sellable_unit == Decimal("11.11")
    # 4. Projected revenue = 90 * 20 = ₹1800.00
    assert res.projected_revenue == Decimal("1800.00")
    # 5. Projected profit = 1800 - 1000 = ₹800.00
    assert res.projected_profit == Decimal("800.00")


def test_wastage_percentage_specification():
    """Test yield calculation when scrap is entered as a percentage."""
    batch = BatchCostingInput(
        batch_name="Gulab Jamun Batch",
        ingredients=[
            IngredientInput(
                name="Mawa & Sugar Syrup",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("500.00"),
            )
        ],
        batch_yield=BatchYieldInput(
            gross_quantity=Decimal("200"),
            scrap_percentage=Decimal("5"),  # 5% broken/sampling = 10 units
            unit_name="pieces",
        ),
    )

    res = calculate_batch(batch)
    assert res.gross_quantity == Decimal("200")
    assert res.scrap_quantity == Decimal("10.00")
    assert res.sellable_quantity == Decimal("190.00")
    # 500 / 190 = 2.6315... -> ₹2.63
    assert res.cost_per_sellable_unit == Decimal("2.63")


def test_direct_wastage_expense_handling():
    """Test optional direct cash wastage (e.g. ruined extra ingredient disposal fee)."""
    batch = BatchCostingInput(
        batch_name="Special Catering Batch",
        ingredients=[
            IngredientInput(
                name="Rice & Spices",
                recipe_quantity=Decimal("1"),
                recipe_unit="unit",
                purchase_price=Decimal("400.00"),
            )
        ],
        direct_wastage_expense=Decimal("50.00"),  # Out of pocket scrap fee
        batch_yield=BatchYieldInput(
            sellable_quantity=Decimal("50"),
            unit_name="boxes",
        ),
    )

    res = calculate_batch(batch)
    # Total cost = 400 + 50 = ₹450
    assert res.total_batch_cost == Decimal("450.00")
    assert res.cost_per_sellable_unit == Decimal("9.00")  # 450 / 50


def test_rounding_half_up_precision():
    """Verify ROUND_HALF_UP rounding behavior for paise amounts."""
    # 0.005 rounds up to 0.01
    assert round_currency(Decimal("10.005")) == Decimal("10.01")
    # 0.004 rounds down to 0.00
    assert round_currency(Decimal("10.004")) == Decimal("10.00")
    # 0.00500001 rounds up to 0.01
    assert round_currency(Decimal("10.00500001")) == Decimal("10.01")

