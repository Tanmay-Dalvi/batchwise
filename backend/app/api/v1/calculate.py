"""Pure calculation API endpoint delegating strictly to the deterministic math engine."""

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.calculator.engine import calculate_batch
from app.calculator.exceptions import (
    BatchwiseError,
    IncompatibleUnitDimensionError,
    InvalidTargetMarginError,
    NegativeValueValidationError,
    UnknownUnitError,
    ZeroYieldError,
)
from app.calculator.models import BatchCalculationResult, BatchCostingInput

router = APIRouter(tags=["calculator"])


@router.post(
    "/calculate",
    response_model=BatchCalculationResult,
    status_code=status.HTTP_200_OK,
    summary="Calculate true batch production cost, unit break-even, and profit metrics",
)
def calculate_batch_endpoint(batch_input: BatchCostingInput) -> BatchCalculationResult:
    """
    Deterministically calculate batch cost, unit economics, profit margins, and step-by-step audit trace.
    Zero floating-point arithmetic. Never trusts AI for mathematical calculations.
    """
    try:
        return calculate_batch(batch_input)
    except (
        ZeroYieldError,
        IncompatibleUnitDimensionError,
        InvalidTargetMarginError,
        NegativeValueValidationError,
        UnknownUnitError,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_type": e.__class__.__name__,
                "message": str(e),
            },
        )
    except BatchwiseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "BatchwiseError",
                "message": str(e),
            },
        )

