"""Pydantic request and response schemas for Recipe and Batch persistence."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.calculator.models import BatchCalculationResult, BatchCostingInput
from app.calculator.units import normalize_unit


class RecipeIngredientBase(BaseModel):
    name: str = Field(..., min_length=1)
    recipe_quantity: Decimal = Field(..., gt=0)
    recipe_unit: str = Field(...)
    purchase_quantity: Optional[Decimal] = Field(default=None, gt=0)
    purchase_unit: Optional[str] = Field(default=None)
    purchase_price: Decimal = Field(..., ge=0)


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientResponse(RecipeIngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipe_id: str
    purchase_quantity: Decimal
    purchase_unit: str


class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Recipe or product name")
    description: Optional[str] = None
    yield_unit: str = Field(default="packets")
    default_packaging_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    default_labour_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    default_fuel_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    default_delivery_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    default_other_expenses: Decimal = Field(default=Decimal("0.00"), ge=0)
    ingredients: List[RecipeIngredientCreate] = Field(default_factory=list)


class RecipeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    yield_unit: Optional[str] = None
    default_packaging_cost: Optional[Decimal] = Field(default=None, ge=0)
    default_labour_cost: Optional[Decimal] = Field(default=None, ge=0)
    default_fuel_cost: Optional[Decimal] = Field(default=None, ge=0)
    default_delivery_cost: Optional[Decimal] = Field(default=None, ge=0)
    default_other_expenses: Optional[Decimal] = Field(default=None, ge=0)
    ingredients: Optional[List[RecipeIngredientCreate]] = None


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    yield_unit: str
    default_packaging_cost: Decimal
    default_labour_cost: Decimal
    default_fuel_cost: Decimal
    default_delivery_cost: Decimal
    default_other_expenses: Decimal
    created_at: datetime
    updated_at: datetime
    ingredients: List[RecipeIngredientResponse]


class BatchRecordCreate(BaseModel):
    """Payload to calculate and persist a batch record in one transaction."""
    batch_costing: BatchCostingInput
    recipe_id: Optional[str] = None
    notes: Optional[str] = None


class BatchRecordSummary(BaseModel):
    """Summary of a saved production batch for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipe_id: Optional[str]
    batch_name: str
    notes: Optional[str]
    total_batch_cost: Decimal
    sellable_quantity: Decimal
    unit_name: str
    cost_per_sellable_unit: Decimal
    planned_selling_price: Optional[Decimal]
    projected_profit: Optional[Decimal]
    profit_margin_pct: Optional[Decimal]
    created_at: datetime
    updated_at: datetime


class BatchRecordDetailResponse(BatchRecordSummary):
    """Complete saved batch detail including full calculation inputs and deterministic outputs."""
    calculation_input: BatchCostingInput
    calculation_result: BatchCalculationResult

