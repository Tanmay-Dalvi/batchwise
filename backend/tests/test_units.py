"""Unit conversion and dimension safety test suite."""

from decimal import Decimal
import pytest

from app.calculator.exceptions import IncompatibleUnitDimensionError, UnknownUnitError
from app.calculator.units import (
    Unit,
    UnitDimension,
    are_units_compatible,
    convert_quantity,
    get_unit_dimension,
    normalize_unit,
)


def test_normalize_unit_aliases():
    """Verify standard and colloquial unit aliases normalize to canonical enums."""
    # Mass
    assert normalize_unit("kg") == Unit.KG
    assert normalize_unit("KGS") == Unit.KG
    assert normalize_unit("kilogram") == Unit.KG
    assert normalize_unit("kilograms") == Unit.KG
    assert normalize_unit("g") == Unit.G
    assert normalize_unit("gm") == Unit.G
    assert normalize_unit("gms") == Unit.G
    assert normalize_unit("gram") == Unit.G

    # Volume
    assert normalize_unit("l") == Unit.L
    assert normalize_unit("L") == Unit.L
    assert normalize_unit("ltr") == Unit.L
    assert normalize_unit("liter") == Unit.L
    assert normalize_unit("litres") == Unit.L
    assert normalize_unit("ml") == Unit.ML
    assert normalize_unit("milliliter") == Unit.ML

    # Count
    assert normalize_unit("unit") == Unit.UNIT
    assert normalize_unit("units") == Unit.UNIT
    assert normalize_unit("piece") == Unit.UNIT
    assert normalize_unit("packet") == Unit.UNIT
    assert normalize_unit("packets") == Unit.UNIT
    assert normalize_unit("pkt") == Unit.UNIT
    assert normalize_unit("dozen") == Unit.DOZEN
    assert normalize_unit("dz") == Unit.DOZEN


def test_unknown_unit_raises():
    """Verify unsupported unit string raises UnknownUnitError."""
    with pytest.raises(UnknownUnitError) as exc_info:
        normalize_unit("cups")
    assert "Unknown or unsupported unit: 'cups'" in str(exc_info.value)


def test_unit_dimensions():
    """Verify units correctly map to physical dimensions."""
    assert get_unit_dimension(Unit.KG) == UnitDimension.MASS
    assert get_unit_dimension(Unit.G) == UnitDimension.MASS
    assert get_unit_dimension(Unit.L) == UnitDimension.VOLUME
    assert get_unit_dimension(Unit.ML) == UnitDimension.VOLUME
    assert get_unit_dimension(Unit.UNIT) == UnitDimension.COUNT
    assert get_unit_dimension(Unit.DOZEN) == UnitDimension.COUNT


def test_are_units_compatible():
    """Verify dimension compatibility check."""
    assert are_units_compatible("kg", "g") is True
    assert are_units_compatible("l", "ml") is True
    assert are_units_compatible("packet", "dozen") is True

    # Incompatible pairs
    assert are_units_compatible("kg", "l") is False
    assert are_units_compatible("g", "ml") is False
    assert are_units_compatible("kg", "packet") is False
    assert are_units_compatible("l", "dozen") is False


def test_valid_conversions_mass():
    """Test exact conversions within mass dimension using Decimal."""
    # 5 kg to g
    assert convert_quantity(Decimal("5"), "kg", "g") == Decimal("5000")
    # 750 g to kg
    assert convert_quantity(Decimal("750"), "g", "kg") == Decimal("0.75")
    # Identity
    assert convert_quantity(Decimal("2.5"), "kg", "kg") == Decimal("2.5")


def test_valid_conversions_volume():
    """Test exact conversions within volume dimension using Decimal."""
    # 2.5 l to ml
    assert convert_quantity(Decimal("2.5"), "l", "ml") == Decimal("2500")
    # 250 ml to l
    assert convert_quantity(Decimal("250"), "ml", "l") == Decimal("0.25")


def test_valid_conversions_count():
    """Test exact conversions within count dimension."""
    # 2 dozen to units
    assert convert_quantity(Decimal("2"), "dozen", "unit") == Decimal("24")
    # 36 units to dozens
    assert convert_quantity(Decimal("36"), "unit", "dozen") == Decimal("3")


def test_incompatible_unit_dimension_rejection():
    """Reject cross-dimensional conversions (e.g. mass to volume) without guessing density."""
    with pytest.raises(IncompatibleUnitDimensionError) as exc_info:
        convert_quantity(Decimal("1"), "kg", "l")
    assert "Cannot convert 'kg' (MASS) to 'l' (VOLUME)" in str(exc_info.value)

    with pytest.raises(IncompatibleUnitDimensionError):
        convert_quantity(Decimal("500"), "ml", "g")

    with pytest.raises(IncompatibleUnitDimensionError):
        convert_quantity(Decimal("10"), "packet", "kg")

