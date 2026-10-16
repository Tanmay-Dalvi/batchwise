"""Batchwise pure financial calculation and unit conversion module."""

from app.calculator.engine import (
    calculate_batch,
    calculate_ingredient_cost,
    round_currency,
    round_percent,
)
from app.calculator.exceptions import (
    BatchwiseError,
    IncompatibleUnitDimensionError,
    InvalidTargetMarginError,
    NegativeValueValidationError,
    UnknownUnitError,
    ZeroYieldError,
)
from app.calculator.models import (
    AuditStep,
    BatchCalculationResult,
    BatchCostingInput,
    BatchYieldInput,
    IngredientCostResult,
    IngredientInput,
)
from app.calculator.units import (
    Unit,
    UnitDimension,
    are_units_compatible,
    convert_quantity,
    get_unit_dimension,
    normalize_unit,
)

__all__ = [
    "calculate_batch",
    "calculate_ingredient_cost",
    "round_currency",
    "round_percent",
    "BatchwiseError",
    "IncompatibleUnitDimensionError",
    "InvalidTargetMarginError",
    "NegativeValueValidationError",
    "UnknownUnitError",
    "ZeroYieldError",
    "AuditStep",
    "BatchCalculationResult",
    "BatchCostingInput",
    "BatchYieldInput",
    "IngredientCostResult",
    "IngredientInput",
    "Unit",
    "UnitDimension",
    "are_units_compatible",
    "convert_quantity",
    "get_unit_dimension",
    "normalize_unit",
]

