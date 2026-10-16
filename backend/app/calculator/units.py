"""Dimension-safe unit conversion system for Batchwise.

Strictly enforces physical dimension boundaries (MASS, VOLUME, COUNT).
Cross-dimensional conversions are rejected to guarantee financial correctness.
"""

from decimal import Decimal
from enum import Enum
from typing import Dict, Tuple

from app.calculator.exceptions import IncompatibleUnitDimensionError, UnknownUnitError


class UnitDimension(str, Enum):
    MASS = "MASS"
    VOLUME = "VOLUME"
    COUNT = "COUNT"


class Unit(str, Enum):
    # Mass
    KG = "kg"
    G = "g"
    # Volume
    L = "l"
    ML = "ml"
    # Count
    UNIT = "unit"
    DOZEN = "dozen"


# Mapping from recognized string aliases to canonical Unit enum
_UNIT_ALIASES: Dict[str, Unit] = {
    # Mass
    "kg": Unit.KG,
    "kgs": Unit.KG,
    "kilogram": Unit.KG,
    "kilograms": Unit.KG,
    "kilo": Unit.KG,
    "kilos": Unit.KG,
    "g": Unit.G,
    "gm": Unit.G,
    "gms": Unit.G,
    "gram": Unit.G,
    "grams": Unit.G,
    # Volume
    "l": Unit.L,
    "ltr": Unit.L,
    "liter": Unit.L,
    "liters": Unit.L,
    "litre": Unit.L,
    "litres": Unit.L,
    "ml": Unit.ML,
    "mls": Unit.ML,
    "milliliter": Unit.ML,
    "milliliters": Unit.ML,
    "millilitre": Unit.ML,
    "millilitres": Unit.ML,
    # Count
    "unit": Unit.UNIT,
    "units": Unit.UNIT,
    "piece": Unit.UNIT,
    "pieces": Unit.UNIT,
    "pc": Unit.UNIT,
    "pcs": Unit.UNIT,
    "packet": Unit.UNIT,
    "packets": Unit.UNIT,
    "pack": Unit.UNIT,
    "packs": Unit.UNIT,
    "pkt": Unit.UNIT,
    "pkts": Unit.UNIT,
    "dozen": Unit.DOZEN,
    "dozens": Unit.DOZEN,
    "dz": Unit.DOZEN,
}

# Dimension and multiplier relative to dimension base (g for MASS, ml for VOLUME, unit for COUNT)
_UNIT_METADATA: Dict[Unit, Tuple[UnitDimension, Decimal]] = {
    Unit.G: (UnitDimension.MASS, Decimal("1")),
    Unit.KG: (UnitDimension.MASS, Decimal("1000")),
    Unit.ML: (UnitDimension.VOLUME, Decimal("1")),
    Unit.L: (UnitDimension.VOLUME, Decimal("1000")),
    Unit.UNIT: (UnitDimension.COUNT, Decimal("1")),
    Unit.DOZEN: (UnitDimension.COUNT, Decimal("12")),
}


def normalize_unit(unit_input: str | Unit) -> Unit:
    """Normalize user or system unit string to canonical Unit enum."""
    if isinstance(unit_input, Unit):
        return unit_input
    
    cleaned = str(unit_input).strip().lower()
    if cleaned in _UNIT_ALIASES:
        return _UNIT_ALIASES[cleaned]
    
    # Try exact match against enum values
    try:
        return Unit(cleaned)
    except ValueError:
        raise UnknownUnitError(unit_input)


def get_unit_dimension(unit_input: str | Unit) -> UnitDimension:
    """Return the physical dimension (MASS, VOLUME, COUNT) of the given unit."""
    canonical = normalize_unit(unit_input)
    return _UNIT_METADATA[canonical][0]


def are_units_compatible(unit_a: str | Unit, unit_b: str | Unit) -> bool:
    """Check if two units belong to the same physical dimension."""
    try:
        dim_a = get_unit_dimension(unit_a)
        dim_b = get_unit_dimension(unit_b)
        return dim_a == dim_b
    except UnknownUnitError:
        return False


def convert_quantity(
    quantity: Decimal,
    from_unit_input: str | Unit,
    to_unit_input: str | Unit
) -> Decimal:
    """
    Convert a quantity from one unit to another within the same dimension.
    
    Raises:
        UnknownUnitError: If either unit is not recognized.
        IncompatibleUnitDimensionError: If attempting cross-dimensional conversion (e.g. kg -> ml).
    """
    if not isinstance(quantity, Decimal):
        quantity = Decimal(str(quantity))

    from_canonical = normalize_unit(from_unit_input)
    to_canonical = normalize_unit(to_unit_input)

    from_dim, from_factor = _UNIT_METADATA[from_canonical]
    to_dim, to_factor = _UNIT_METADATA[to_canonical]

    if from_dim != to_dim:
        raise IncompatibleUnitDimensionError(
            from_unit=from_canonical.value,
            to_unit=to_canonical.value,
            from_dim=from_dim.value,
            to_dim=to_dim.value,
        )

    if from_canonical == to_canonical:
        return quantity

    # Convert to base unit, then to target unit
    base_quantity = quantity * from_factor
    return base_quantity / to_factor

