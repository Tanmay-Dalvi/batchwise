"""Custom exceptions for Batchwise pure financial calculation engine."""

class BatchwiseError(Exception):
    """Base exception for all Batchwise domain errors."""
    pass


class IncompatibleUnitDimensionError(BatchwiseError):
    """Raised when attempting to convert between incompatible physical dimensions."""
    def __init__(self, from_unit: str, to_unit: str, from_dim: str, to_dim: str):
        super().__init__(
            f"Cannot convert '{from_unit}' ({from_dim}) to '{to_unit}' ({to_dim}). "
            f"Batchwise rejects cross-dimensional conversion without explicit conversion factors."
        )
        self.from_unit = from_unit
        self.to_unit = to_unit
        self.from_dim = from_dim
        self.to_dim = to_dim


class UnknownUnitError(BatchwiseError):
    """Raised when an unrecognized unit identifier is provided."""
    def __init__(self, unit: str):
        super().__init__(
            f"Unknown or unsupported unit: '{unit}'. "
            f"Supported units are: Mass (kg, g), Volume (l, ml), and Count (unit/piece/packet, dozen)."
        )
        self.unit = unit


class ZeroYieldError(BatchwiseError):
    """Raised when sellable quantity is zero or negative."""
    def __init__(self, message: str = "Sellable batch quantity must be strictly greater than zero to calculate per-unit cost and break-even price."):
        super().__init__(message)


class InvalidTargetMarginError(BatchwiseError):
    """Raised when target margin percentage is outside the valid range [0, 100)."""
    def __init__(self, margin_pct: str):
        super().__init__(
            f"Invalid target margin: {margin_pct}%. "
            f"Target profit margin must be greater than or equal to 0% and strictly less than 100%."
        )
        self.margin_pct = margin_pct


class NegativeValueValidationError(BatchwiseError):
    """Raised when an expense, quantity, or price is negative."""
    def __init__(self, field_name: str, value: str):
        super().__init__(f"Field '{field_name}' cannot be negative (received {value}).")
        self.field_name = field_name
        self.value = value

