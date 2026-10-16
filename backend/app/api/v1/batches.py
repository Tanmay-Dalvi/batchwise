"""Batch costing production runs persistence endpoints."""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.calculator.engine import calculate_batch
from app.calculator.models import BatchCalculationResult, BatchCostingInput
from app.db.crud import (
    create_batch_record,
    delete_batch_record,
    get_batch_record,
    list_batch_records,
    update_batch_record,
)
from app.db.database import get_db
from app.db.models import BatchRecord
from app.schemas.records import (
    BatchRecordCreate,
    BatchRecordDetailResponse,
    BatchRecordSummary,
)

router = APIRouter(prefix="/batches", tags=["batches"])


def _to_detail(batch: BatchRecord) -> BatchRecordDetailResponse:
    calc_in = BatchCostingInput.model_validate_json(batch.calculation_input_json)
    calc_res = BatchCalculationResult.model_validate_json(batch.calculation_result_json)
    return BatchRecordDetailResponse(
        id=batch.id,
        recipe_id=batch.recipe_id,
        batch_name=batch.batch_name,
        notes=batch.notes,
        total_batch_cost=Decimal(batch.total_batch_cost),
        sellable_quantity=Decimal(batch.sellable_quantity),
        unit_name=batch.unit_name,
        cost_per_sellable_unit=Decimal(batch.cost_per_sellable_unit),
        planned_selling_price=Decimal(batch.planned_selling_price) if batch.planned_selling_price else None,
        projected_profit=Decimal(batch.projected_profit) if batch.projected_profit else None,
        profit_margin_pct=Decimal(batch.profit_margin_pct) if batch.profit_margin_pct else None,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        calculation_input=calc_in,
        calculation_result=calc_res,
    )


def _to_summary(batch: BatchRecord) -> BatchRecordSummary:
    return BatchRecordSummary(
        id=batch.id,
        recipe_id=batch.recipe_id,
        batch_name=batch.batch_name,
        notes=batch.notes,
        total_batch_cost=Decimal(batch.total_batch_cost),
        sellable_quantity=Decimal(batch.sellable_quantity),
        unit_name=batch.unit_name,
        cost_per_sellable_unit=Decimal(batch.cost_per_sellable_unit),
        planned_selling_price=Decimal(batch.planned_selling_price) if batch.planned_selling_price else None,
        projected_profit=Decimal(batch.projected_profit) if batch.projected_profit else None,
        profit_margin_pct=Decimal(batch.profit_margin_pct) if batch.profit_margin_pct else None,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.post("", response_model=BatchRecordDetailResponse, status_code=status.HTTP_201_CREATED)
def create_batch_endpoint(
    batch_in: BatchRecordCreate, db: Session = Depends(get_db)
) -> BatchRecordDetailResponse:
    """Calculate and save a production batch record with its full audit trail."""
    calculation_res = calculate_batch(batch_in.batch_costing)
    saved_batch = create_batch_record(
        db=db,
        batch_input=batch_in.batch_costing,
        calculation_result=calculation_res,
        recipe_id=batch_in.recipe_id,
        notes=batch_in.notes,
    )
    return _to_detail(saved_batch)


@router.get("", response_model=List[BatchRecordSummary])
def list_batches_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    recipe_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[BatchRecordSummary]:
    """List historical batch records ordered by latest first."""
    batches = list_batch_records(db=db, skip=skip, limit=limit, recipe_id=recipe_id)
    return [_to_summary(b) for b in batches]


@router.get("/{batch_id}", response_model=BatchRecordDetailResponse)
def get_batch_endpoint(
    batch_id: str, db: Session = Depends(get_db)
) -> BatchRecordDetailResponse:
    """Retrieve full batch calculation snapshot and audit history."""
    batch = get_batch_record(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch record '{batch_id}' not found.",
        )
    return _to_detail(batch)


@router.put("/{batch_id}", response_model=BatchRecordDetailResponse)
def update_batch_endpoint(
    batch_id: str, batch_in: BatchRecordCreate, db: Session = Depends(get_db)
) -> BatchRecordDetailResponse:
    """Recalculate and update an existing batch record."""
    calculation_res = calculate_batch(batch_in.batch_costing)
    updated = update_batch_record(
        db=db,
        batch_id=batch_id,
        batch_input=batch_in.batch_costing,
        calculation_result=calculation_res,
        notes=batch_in.notes,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch record '{batch_id}' not found.",
        )
    return _to_detail(updated)


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_endpoint(
    batch_id: str, db: Session = Depends(get_db)
) -> None:
    """Delete a saved batch record."""
    deleted = delete_batch_record(db=db, batch_id=batch_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch record '{batch_id}' not found.",
        )

