"""Pure Python deterministic financial calculation engine for Batchwise.

Implements all financial mathematics strictly in Decimal arithmetic.
Includes full step-by-step audit logging and zero floating-point math.
"""

from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from typing import List, Optional, Tuple

from app.calculator.exceptions import (
    InvalidTargetMarginError,
    ZeroYieldError,
)
from app.calculator.models import (
    AuditStep,
    BatchCalculationResult,
    BatchCostingInput,
    IngredientCostResult,
    IngredientInput,
)
from app.calculator.units import convert_quantity, normalize_unit

# Rounding constants
CURRENCY_PRECISION = Decimal("0.01")
PERCENT_PRECISION = Decimal("0.01")
UNIT_COUNT_PRECISION = Decimal("1")


def round_currency(value: Decimal) -> Decimal:
    """Round a monetary Decimal value to 2 decimal places (paise/cents) using ROUND_HALF_UP."""
    return value.quantize(CURRENCY_PRECISION, rounding=ROUND_HALF_UP)


def round_percent(value: Decimal) -> Decimal:
    """Round a percentage Decimal value to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(PERCENT_PRECISION, rounding=ROUND_HALF_UP)


def calculate_ingredient_cost(ingredient: IngredientInput) -> IngredientCostResult:
    """
    Calculate the exact and display cost of an ingredient used in a recipe.
    
    Converts purchase quantity and recipe quantity to canonical base units,
    computes the exact usage ratio, and multiplies by the purchase price.
    """
    recipe_u = normalize_unit(ingredient.recipe_unit)
    purchase_u = normalize_unit(ingredient.purchase_unit)

    # Convert recipe quantity into the purchase unit to determine consumption ratio
    recipe_qty_in_purchase_units = convert_quantity(
        quantity=ingredient.recipe_quantity,
        from_unit_input=recipe_u,
        to_unit_input=purchase_u,
    )

    ratio = recipe_qty_in_purchase_units / ingredient.purchase_quantity
    # Multiply before dividing to prevent premature precision loss on recurring fractions (e.g. 1/3, 1/6)
    exact_cost = (ingredient.purchase_price * recipe_qty_in_purchase_units) / ingredient.purchase_quantity
    display_cost = round_currency(exact_cost)

    explanation = (
        f"Used {ingredient.recipe_quantity} {recipe_u.value} "
        f"(converted to {recipe_qty_in_purchase_units} {purchase_u.value}) "
        f"out of {ingredient.purchase_quantity} {purchase_u.value} purchased for ₹{ingredient.purchase_price}. "
        f"Usage ratio: {round_percent(ratio * Decimal('100'))}%. Total cost: ₹{display_cost}."
    )

    audit = AuditStep(
        step_name=f"INGREDIENT_COST:{ingredient.name}",
        formula="purchase_price * (convert(recipe_quantity, purchase_unit) / purchase_quantity)",
        inputs={
            "recipe_quantity": str(ingredient.recipe_quantity),
            "recipe_unit": recipe_u.value,
            "purchase_quantity": str(ingredient.purchase_quantity),
            "purchase_unit": purchase_u.value,
            "purchase_price": str(ingredient.purchase_price),
            "recipe_in_purchase_units": str(recipe_qty_in_purchase_units),
        },
        result=str(display_cost),
        explanation=explanation,
    )

    return IngredientCostResult(
        name=ingredient.name,
        recipe_quantity=ingredient.recipe_quantity,
        recipe_unit=recipe_u.value,
        purchase_quantity=ingredient.purchase_quantity,
        purchase_unit=purchase_u.value,
        purchase_price=ingredient.purchase_price,
        cost=display_cost,
        exact_cost=exact_cost,
        audit_step=audit,
    )


def calculate_batch(input_data: BatchCostingInput) -> BatchCalculationResult:
    """
    Perform a complete, deterministic batch calculation with full audit trail.
    
    Guarantees:
    - 100% Decimal precision throughout
    - Never double-counts wastage
    - Strict distinction between profit margin and markup
    - Explicit division-by-zero guards
    """
    audit_trail: List[AuditStep] = []

    # 1. Ingredient Costs
    ingredient_results: List[IngredientCostResult] = []
    exact_ingredients_cost = Decimal("0.00")

    for ing in input_data.ingredients:
        res = calculate_ingredient_cost(ing)
        ingredient_results.append(res)
        exact_ingredients_cost += res.exact_cost
        audit_trail.append(res.audit_step)

    display_ingredients_cost = round_currency(exact_ingredients_cost)

    # 2. Overheads
    total_overheads = (
        input_data.packaging_cost
        + input_data.labour_cost
        + input_data.fuel_cost
        + input_data.delivery_cost
        + input_data.other_expenses
        + input_data.direct_wastage_expense
    )

    exact_total_batch_cost = exact_ingredients_cost + total_overheads
    display_total_batch_cost = round_currency(exact_total_batch_cost)

    audit_trail.append(
        AuditStep(
            step_name="TOTAL_BATCH_COST",
            formula="sum(ingredient_costs) + packaging + labour + fuel + delivery + other + direct_wastage",
            inputs={
                "ingredients_cost": str(display_ingredients_cost),
                "packaging_cost": str(input_data.packaging_cost),
                "labour_cost": str(input_data.labour_cost),
                "fuel_cost": str(input_data.fuel_cost),
                "delivery_cost": str(input_data.delivery_cost),
                "other_expenses": str(input_data.other_expenses),
                "direct_wastage_expense": str(input_data.direct_wastage_expense),
            },
            result=str(display_total_batch_cost),
            explanation=(
                f"Summed total ingredients (₹{display_ingredients_cost}) and total overheads "
                f"(₹{round_currency(total_overheads)}) to arrive at total batch cost of ₹{display_total_batch_cost}."
            ),
        )
    )

    # 3. Yield & Sellable Quantity
    sellable_qty = input_data.batch_yield.sellable_quantity
    if sellable_qty is None or sellable_qty <= Decimal("0"):
        raise ZeroYieldError("Batch has zero or negative sellable quantity. Cannot compute unit cost.")

    # 4. Unit Cost & Break-Even Selling Price
    exact_unit_cost = exact_total_batch_cost / sellable_qty
    display_unit_cost = round_currency(exact_unit_cost)
    break_even_price = display_unit_cost

    audit_trail.append(
        AuditStep(
            step_name="UNIT_COST_AND_BREAK_EVEN",
            formula="total_batch_cost / sellable_quantity",
            inputs={
                "total_batch_cost": str(display_total_batch_cost),
                "sellable_quantity": str(sellable_qty),
            },
            result=str(display_unit_cost),
            explanation=(
                f"Divided total batch cost (₹{display_total_batch_cost}) by {sellable_qty} "
                f"{input_data.batch_yield.unit_name} to get production cost of ₹{display_unit_cost} per {input_data.batch_yield.unit_name}. "
                f"Break-even selling price is exactly ₹{break_even_price}."
            ),
        )
    )

    # 5. Projections at Planned Selling Price (if provided)
    planned_price = input_data.planned_selling_price
    projected_revenue: Optional[Decimal] = None
    projected_profit: Optional[Decimal] = None
    profit_per_unit: Optional[Decimal] = None
    profit_margin_pct: Optional[Decimal] = None
    markup_pct: Optional[Decimal] = None
    break_even_units: Optional[Decimal] = None

    if planned_price is not None:
        exact_revenue = planned_price * sellable_qty
        projected_revenue = round_currency(exact_revenue)

        exact_profit = exact_revenue - exact_total_batch_cost
        projected_profit = round_currency(exact_profit)

        exact_profit_per_unit = planned_price - exact_unit_cost
        profit_per_unit = round_currency(exact_profit_per_unit)

        # Margin: (Profit / Revenue) * 100
        if exact_revenue > Decimal("0"):
            exact_margin = (exact_profit / exact_revenue) * Decimal("100")
            profit_margin_pct = round_percent(exact_margin)
        else:
            profit_margin_pct = None

        # Markup: (Profit / Cost) * 100
        if exact_total_batch_cost > Decimal("0"):
            exact_markup = (exact_profit / exact_total_batch_cost) * Decimal("100")
            markup_pct = round_percent(exact_markup)
        else:
            markup_pct = None

        # Break-even units to sell
        if planned_price > Decimal("0"):
            break_even_units = (exact_total_batch_cost / planned_price).quantize(
                UNIT_COUNT_PRECISION, rounding=ROUND_CEILING
            )
        else:
            break_even_units = None

        audit_trail.append(
            AuditStep(
                step_name="PRICING_AND_MARGIN_PROJECTION",
                formula=(
                    "Revenue = P_sell * Q_sellable; Profit = Revenue - C_batch; "
                    "Margin = (Profit / Revenue) * 100; Markup = (Profit / C_batch) * 100"
                ),
                inputs={
                    "planned_selling_price": str(planned_price),
                    "sellable_quantity": str(sellable_qty),
                    "total_batch_cost": str(display_total_batch_cost),
                },
                result=(
                    f"Revenue: ₹{projected_revenue}, Profit: ₹{projected_profit}, "
                    f"Margin: {profit_margin_pct}%, Markup: {markup_pct}%"
                ),
                explanation=(
                    f"At planned selling price of ₹{planned_price} per unit, projected revenue across "
                    f"{sellable_qty} units is ₹{projected_revenue}. Net batch profit is ₹{projected_profit} "
                    f"(₹{profit_per_unit} per unit). Profit margin is {profit_margin_pct}% of revenue "
                    f"(equivalent to a {markup_pct}% markup over cost). "
                    f"Must sell at least {break_even_units} units to break even on batch expenses."
                ),
            )
        )

    # 6. Target Margin Recommendation (if provided)
    target_margin_pct = input_data.target_margin_pct
    target_margin_price: Optional[Decimal] = None
    target_profit_per_unit: Optional[Decimal] = None
    target_markup_pct: Optional[Decimal] = None

    if target_margin_pct is not None:
        if target_margin_pct < Decimal("0") or target_margin_pct >= Decimal("100"):
            raise InvalidTargetMarginError(str(target_margin_pct))

        # Formula: Unit Cost / (1 - Target Margin / 100)
        margin_decimal = target_margin_pct / Decimal("100")
        divisor = Decimal("1") - margin_decimal
        exact_target_price = exact_unit_cost / divisor
        target_margin_price = round_currency(exact_target_price)
        target_profit_per_unit = round_currency(target_margin_price - display_unit_cost)

        # Equivalent markup = (Target Margin / (100 - Target Margin)) * 100
        exact_target_markup = (target_margin_pct / (Decimal("100") - target_margin_pct)) * Decimal("100")
        target_markup_pct = round_percent(exact_target_markup)

        audit_trail.append(
            AuditStep(
                step_name="TARGET_MARGIN_RECOMMENDATION",
                formula="P_target = Unit_Cost / (1 - (Target_Margin / 100))",
                inputs={
                    "unit_cost": str(display_unit_cost),
                    "target_margin_pct": str(target_margin_pct),
                },
                result=f"Target Price: ₹{target_margin_price} (Markup: {target_markup_pct}%)",
                explanation=(
                    f"To achieve a true profit margin of {target_margin_pct}%, the selling price must be "
                    f"₹{target_margin_price} (profit of ₹{target_profit_per_unit} per unit). "
                    f"Notice that a {target_margin_pct}% margin corresponds to a {target_markup_pct}% markup on cost."
                ),
            )
        )

    # 7. Realized Sales Performance (if actual_units_sold provided)
    actual_sold = input_data.actual_units_sold
    unsold_units: Optional[Decimal] = None
    realized_revenue: Optional[Decimal] = None
    cogs_sold: Optional[Decimal] = None
    realized_gross_profit: Optional[Decimal] = None
    net_cashflow: Optional[Decimal] = None
    unsold_inventory_cost_val: Optional[Decimal] = None

    if actual_sold is not None:
        unsold_units = sellable_qty - actual_sold
        effective_price = planned_price if planned_price is not None else Decimal("0.00")
        
        exact_realized_rev = actual_sold * effective_price
        realized_revenue = round_currency(exact_realized_rev)

        exact_cogs = actual_sold * exact_unit_cost
        cogs_sold = round_currency(exact_cogs)

        realized_gross_profit = round_currency(exact_realized_rev - exact_cogs)
        net_cashflow = round_currency(exact_realized_rev - exact_total_batch_cost)
        unsold_inventory_cost_val = round_currency(unsold_units * exact_unit_cost)

        audit_trail.append(
            AuditStep(
                step_name="REALIZED_SALES_PERFORMANCE",
                formula="Realized_Rev = Units_Sold * P_sell; Net_Cashflow = Realized_Rev - C_batch",
                inputs={
                    "actual_units_sold": str(actual_sold),
                    "selling_price": str(effective_price),
                    "total_batch_cost": str(display_total_batch_cost),
                    "unsold_units": str(unsold_units),
                },
                result=f"Cashflow: ₹{net_cashflow}, Inventory Value: ₹{unsold_inventory_cost_val}",
                explanation=(
                    f"Sold {actual_sold} of {sellable_qty} {input_data.batch_yield.unit_name}. "
                    f"Collected ₹{realized_revenue} in cash. Cost of Goods Sold for these units: ₹{cogs_sold}. "
                    f"Realized gross profit on sold units: ₹{realized_gross_profit}. "
                    f"Net cash recovery against batch outlay: ₹{net_cashflow}. "
                    f"Remaining unsold inventory: {unsold_units} units valued at ₹{unsold_inventory_cost_val}."
                ),
            )
        )

    return BatchCalculationResult(
        batch_name=input_data.batch_name,
        unit_name=input_data.batch_yield.unit_name,
        total_ingredients_cost=display_ingredients_cost,
        packaging_cost=input_data.packaging_cost,
        labour_cost=input_data.labour_cost,
        fuel_cost=input_data.fuel_cost,
        delivery_cost=input_data.delivery_cost,
        other_expenses=input_data.other_expenses,
        direct_wastage_expense=input_data.direct_wastage_expense,
        total_overheads=round_currency(total_overheads),
        total_batch_cost=display_total_batch_cost,
        gross_quantity=input_data.batch_yield.gross_quantity,
        scrap_quantity=input_data.batch_yield.scrap_quantity,
        sellable_quantity=sellable_qty,
        cost_per_sellable_unit=display_unit_cost,
        break_even_price_per_unit=break_even_price,
        planned_selling_price=planned_price,
        projected_revenue=projected_revenue,
        projected_profit=projected_profit,
        profit_per_unit=profit_per_unit,
        profit_margin_pct=profit_margin_pct,
        markup_pct=markup_pct,
        break_even_units_to_sell=break_even_units,
        target_margin_pct=target_margin_pct,
        target_margin_selling_price=target_margin_price,
        target_margin_profit_per_unit=target_profit_per_unit,
        target_margin_markup_pct=target_markup_pct,
        actual_units_sold=actual_sold,
        unsold_units=unsold_units,
        realized_revenue=realized_revenue,
        cogs_sold_units=cogs_sold,
        realized_gross_profit=realized_gross_profit,
        net_cashflow=net_cashflow,
        unsold_inventory_cost_value=unsold_inventory_cost_val,
        ingredient_results=ingredient_results,
        audit_trail=audit_trail,
    )
