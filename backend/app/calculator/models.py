"""Validated Pydantic models for Batchwise financial calculation engine.

All numerical money and quantity values use Decimal.
Float values are strictly disallowed to prevent binary precision loss.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.calculator.exceptions import (
    InvalidTargetMarginError,
    NegativeValueValidationError,
    ZeroYieldError,
)
from app.calculator.units import Unit, normalize_unit


class AuditStep(BaseModel):
    """Transparent calculation audit step recording formula, inputs, and rationale."""
    model_config = ConfigDict(frozen=True)

    step_name: str
    formula: str
    inputs: Dict[str, str]
    result: str
    explanation: str


class IngredientInput(BaseModel):
    """Specification of an ingredient used in a production batch."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., min_length=1, description="Ingredient name (e.g. Besan, Oil)")
    recipe_quantity: Decimal = Field(..., gt=0, description="Quantity required in the recipe")
    recipe_unit: str = Field(..., description="Unit of recipe quantity (e.g. kg, g, l, ml)")
    purchase_quantity: Optional[Decimal] = Field(
        default=None, gt=0, description="Quantity purchased (defaults to recipe_quantity if bought for batch)"
    )
    purchase_unit: Optional[str] = Field(
        default=None, description="Unit of purchase quantity (defaults to recipe_unit)"
    )
    purchase_price: Decimal = Field(..., ge=0, description="Total price paid for the purchase quantity in ₹")

    @model_validator(mode="after")
    def populate_defaults_and_validate_units(self) -> "IngredientInput":
        # Normalize recipe unit
        normalize_unit(self.recipe_unit)

        # Default purchase quantity & unit to recipe quantity & unit if not specified
        if self.purchase_quantity is None:
            self.purchase_quantity = self.recipe_quantity
        if self.purchase_unit is None:
            self.purchase_unit = self.recipe_unit

        normalize_unit(self.purchase_unit)
        return self


class IngredientCostResult(BaseModel):
    """Calculated cost for an ingredient with its audit step."""
    model_config = ConfigDict(frozen=True)

    name: str
    recipe_quantity: Decimal
    recipe_unit: str
    purchase_quantity: Decimal
    purchase_unit: str
    purchase_price: Decimal
    cost: Decimal  # Display cost rounded to 2 decimal places
    exact_cost: Decimal  # High-precision Decimal for downstream aggregation
    audit_step: AuditStep


class BatchYieldInput(BaseModel):
    """Output yield specification for a batch, accounting for physical scrap."""
    sellable_quantity: Optional[Decimal] = Field(
        default=None, ge=0, description="Direct count of final packaged sellable units"
    )
    gross_quantity: Optional[Decimal] = Field(
        default=None, ge=0, description="Total raw units produced before scrap"
    )
    scrap_quantity: Optional[Decimal] = Field(
        default=None, ge=0, description="Defective, burnt, or sampling units scrapped"
    )
    scrap_percentage: Optional[Decimal] = Field(
        default=None, ge=0, le=100, description="Percentage of gross production scrapped"
    )
    unit_name: str = Field(default="packets", description="Descriptor for sellable units (packets, boxes, pieces)")

    @model_validator(mode="after")
    def compute_effective_sellable_quantity(self) -> "BatchYieldInput":
        if self.sellable_quantity is not None:
            if self.sellable_quantity <= 0:
                raise ZeroYieldError("Sellable quantity must be strictly greater than zero.")
            return self

        if self.gross_quantity is None or self.gross_quantity <= 0:
            raise ZeroYieldError("Either sellable_quantity or gross_quantity (>0) must be specified.")

        gross = self.gross_quantity
        scrap = Decimal("0")

        if self.scrap_quantity is not None:
            scrap += self.scrap_quantity
        elif self.scrap_percentage is not None:
            scrap += (gross * self.scrap_percentage) / Decimal("100")

        if scrap > gross:
            raise NegativeValueValidationError(
                "scrap_quantity", f"{scrap} exceeds gross quantity {gross}"
            )

        effective_sellable = gross - scrap
        if effective_sellable <= 0:
            raise ZeroYieldError("Effective sellable quantity after scrap is zero or negative.")

        self.sellable_quantity = effective_sellable
        self.scrap_quantity = scrap
        return self


class BatchCostingInput(BaseModel):
    """Complete specification of a production batch for financial calculation."""
    batch_name: str = Field(..., min_length=1, description="Batch / Recipe Name (e.g. Diwali Chakli Batch #1)")
    ingredients: List[IngredientInput] = Field(..., min_length=1, description="List of batch ingredients")
    packaging_cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Packaging materials (boxes, pouches, labels)")
    labour_cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Labour cost (owner hours or hired helper)")
    fuel_cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Fuel / energy (LPG cylinder fraction, electricity)")
    delivery_cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Delivery, shipping, or travel expenses")
    other_expenses: Decimal = Field(default=Decimal("0.00"), ge=0, description="Other miscellaneous batch overheads")
    direct_wastage_expense: Decimal = Field(default=Decimal("0.00"), ge=0, description="Out-of-pocket scrap disposal or spoiled extras (₹)")
    batch_yield: BatchYieldInput = Field(..., description="Batch yield and sellable unit specification")
    planned_selling_price: Optional[Decimal] = Field(default=None, ge=0, description="Planned or current selling price per unit in ₹")
    target_margin_pct: Optional[Decimal] = Field(default=None, description="Target profit margin percentage [0, 100)")
    actual_units_sold: Optional[Decimal] = Field(default=None, ge=0, description="Actual units sold to date from this batch")

    @field_validator("target_margin_pct")
    @classmethod
    def validate_target_margin(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < 0 or v >= 100:
                raise InvalidTargetMarginError(str(v))
        return v

    @model_validator(mode="after")
    def validate_sold_units(self) -> "BatchCostingInput":
        if self.actual_units_sold is not None and self.batch_yield.sellable_quantity is not None:
            if self.actual_units_sold > self.batch_yield.sellable_quantity:
                raise NegativeValueValidationError(
                    "actual_units_sold",
                    f"Actual units sold ({self.actual_units_sold}) cannot exceed sellable batch quantity ({self.batch_yield.sellable_quantity})"
                )
        return self


class BatchCalculationResult(BaseModel):
    """Complete, deterministic financial calculation result with audit trace."""
    model_config = ConfigDict(frozen=True)

    batch_name: str
    unit_name: str

    # Cost totals (₹)
    total_ingredients_cost: Decimal
    packaging_cost: Decimal
    labour_cost: Decimal
    fuel_cost: Decimal
    delivery_cost: Decimal
    other_expenses: Decimal
    direct_wastage_expense: Decimal
    total_overheads: Decimal
    total_batch_cost: Decimal

    # Yield
    gross_quantity: Optional[Decimal]
    scrap_quantity: Optional[Decimal]
    sellable_quantity: Decimal

    # Per-unit economics
    cost_per_sellable_unit: Decimal
    break_even_price_per_unit: Decimal

    # Pricing & Profit projections (if planned_selling_price provided)
    planned_selling_price: Optional[Decimal]
    projected_revenue: Optional[Decimal]
    projected_profit: Optional[Decimal]
    profit_per_unit: Optional[Decimal]
    profit_margin_pct: Optional[Decimal]
    markup_pct: Optional[Decimal]
    break_even_units_to_sell: Optional[Decimal]

    # Target margin recommendation (if target_margin_pct provided)
    target_margin_pct: Optional[Decimal]
    target_margin_selling_price: Optional[Decimal]
    target_margin_profit_per_unit: Optional[Decimal]
    target_margin_markup_pct: Optional[Decimal]

    # Realized sales performance (if actual_units_sold provided)
    actual_units_sold: Optional[Decimal]
    unsold_units: Optional[Decimal]
    realized_revenue: Optional[Decimal]
    cogs_sold_units: Optional[Decimal]
    realized_gross_profit: Optional[Decimal]
    net_cashflow: Optional[Decimal]
    unsold_inventory_cost_value: Optional[Decimal]

    # Detailed line items & audit log
    ingredient_results: List[IngredientCostResult]
    audit_trail: List[AuditStep]

