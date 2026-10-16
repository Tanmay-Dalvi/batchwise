"""Database CRUD operations with parameterized transactions for Recipes and Batches."""

import json
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.calculator.models import BatchCalculationResult, BatchCostingInput
from app.db.models import BatchRecord, Recipe, RecipeIngredient
from app.schemas.records import RecipeCreate, RecipeUpdate


# --- Recipe CRUD ---

def create_recipe(db: Session, recipe_in: RecipeCreate) -> Recipe:
    """Create a new recipe template and its associated ingredients in a transaction."""
    recipe = Recipe(
        name=recipe_in.name,
        description=recipe_in.description,
        yield_unit=recipe_in.yield_unit,
        default_packaging_cost=str(recipe_in.default_packaging_cost),
        default_labour_cost=str(recipe_in.default_labour_cost),
        default_fuel_cost=str(recipe_in.default_fuel_cost),
        default_delivery_cost=str(recipe_in.default_delivery_cost),
        default_other_expenses=str(recipe_in.default_other_expenses),
    )
    db.add(recipe)
    db.flush()  # Populates recipe.id for child FK

    for ing in recipe_in.ingredients:
        p_qty = ing.purchase_quantity if ing.purchase_quantity is not None else ing.recipe_quantity
        p_unit = ing.purchase_unit if ing.purchase_unit is not None else ing.recipe_unit
        recipe_ing = RecipeIngredient(
            recipe_id=recipe.id,
            name=ing.name,
            recipe_quantity=str(ing.recipe_quantity),
            recipe_unit=ing.recipe_unit,
            purchase_quantity=str(p_qty),
            purchase_unit=p_unit,
            purchase_price=str(ing.purchase_price),
        )
        db.add(recipe_ing)

    db.commit()
    db.refresh(recipe)
    return recipe


def get_recipe(db: Session, recipe_id: str) -> Optional[Recipe]:
    """Retrieve a recipe by ID with its ingredients eagerly loaded."""
    stmt = (
        select(Recipe)
        .options(joinedload(Recipe.ingredients))
        .where(Recipe.id == recipe_id)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def list_recipes(db: Session, skip: int = 0, limit: int = 100) -> List[Recipe]:
    """List saved recipes ordered by latest update."""
    stmt = (
        select(Recipe)
        .options(joinedload(Recipe.ingredients))
        .order_by(Recipe.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).unique().scalars().all())


def update_recipe(db: Session, recipe_id: str, recipe_in: RecipeUpdate) -> Optional[Recipe]:
    """Update an existing recipe template and optionally replace its ingredient list."""
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return None

    if recipe_in.name is not None:
        recipe.name = recipe_in.name
    if recipe_in.description is not None:
        recipe.description = recipe_in.description
    if recipe_in.yield_unit is not None:
        recipe.yield_unit = recipe_in.yield_unit
    if recipe_in.default_packaging_cost is not None:
        recipe.default_packaging_cost = str(recipe_in.default_packaging_cost)
    if recipe_in.default_labour_cost is not None:
        recipe.default_labour_cost = str(recipe_in.default_labour_cost)
    if recipe_in.default_fuel_cost is not None:
        recipe.default_fuel_cost = str(recipe_in.default_fuel_cost)
    if recipe_in.default_delivery_cost is not None:
        recipe.default_delivery_cost = str(recipe_in.default_delivery_cost)
    if recipe_in.default_other_expenses is not None:
        recipe.default_other_expenses = str(recipe_in.default_other_expenses)

    if recipe_in.ingredients is not None:
        # Clear existing ingredients and replace with updated ones
        recipe.ingredients.clear()
        for ing in recipe_in.ingredients:
            p_qty = ing.purchase_quantity if ing.purchase_quantity is not None else ing.recipe_quantity
            p_unit = ing.purchase_unit if ing.purchase_unit is not None else ing.recipe_unit
            new_ing = RecipeIngredient(
                recipe_id=recipe.id,
                name=ing.name,
                recipe_quantity=str(ing.recipe_quantity),
                recipe_unit=ing.recipe_unit,
                purchase_quantity=str(p_qty),
                purchase_unit=p_unit,
                purchase_price=str(ing.purchase_price),
            )
            recipe.ingredients.append(new_ing)

    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: str) -> bool:
    """Delete a recipe template. Associated ingredients cascade-delete; batches retain unlinked records."""
    recipe = get_recipe(db, recipe_id)
    if not recipe:
        return False
    db.delete(recipe)
    db.commit()
    return True


# --- Batch Record CRUD ---

def create_batch_record(
    db: Session,
    batch_input: BatchCostingInput,
    calculation_result: BatchCalculationResult,
    recipe_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> BatchRecord:
    """Save an immutable production batch run and its exact calculation snapshot."""
    input_json = json.dumps(batch_input.model_dump(mode="json"))
    result_json = json.dumps(calculation_result.model_dump(mode="json"))

    batch = BatchRecord(
        recipe_id=recipe_id,
        batch_name=batch_input.batch_name,
        notes=notes,
        calculation_input_json=input_json,
        calculation_result_json=result_json,
        total_batch_cost=str(calculation_result.total_batch_cost),
        sellable_quantity=str(calculation_result.sellable_quantity),
        unit_name=calculation_result.unit_name,
        cost_per_sellable_unit=str(calculation_result.cost_per_sellable_unit),
        planned_selling_price=str(calculation_result.planned_selling_price) if calculation_result.planned_selling_price is not None else None,
        projected_profit=str(calculation_result.projected_profit) if calculation_result.projected_profit is not None else None,
        profit_margin_pct=str(calculation_result.profit_margin_pct) if calculation_result.profit_margin_pct is not None else None,
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def get_batch_record(db: Session, batch_id: str) -> Optional[BatchRecord]:
    """Retrieve a single batch record by ID."""
    stmt = select(BatchRecord).where(BatchRecord.id == batch_id)
    return db.execute(stmt).scalar_one_or_none()


def list_batch_records(
    db: Session, skip: int = 0, limit: int = 100, recipe_id: Optional[str] = None
) -> List[BatchRecord]:
    """List batch records ordered by latest creation."""
    stmt = select(BatchRecord).order_by(BatchRecord.created_at.desc())
    if recipe_id is not None:
        stmt = stmt.where(BatchRecord.recipe_id == recipe_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_batch_record(
    db: Session,
    batch_id: str,
    batch_input: BatchCostingInput,
    calculation_result: BatchCalculationResult,
    notes: Optional[str] = None,
) -> Optional[BatchRecord]:
    """Update a batch record with a recalculated snapshot."""
    batch = get_batch_record(db, batch_id)
    if not batch:
        return None

    batch.batch_name = batch_input.batch_name
    if notes is not None:
        batch.notes = notes
    batch.calculation_input_json = json.dumps(batch_input.model_dump(mode="json"))
    batch.calculation_result_json = json.dumps(calculation_result.model_dump(mode="json"))
    batch.total_batch_cost = str(calculation_result.total_batch_cost)
    batch.sellable_quantity = str(calculation_result.sellable_quantity)
    batch.unit_name = calculation_result.unit_name
    batch.cost_per_sellable_unit = str(calculation_result.cost_per_sellable_unit)
    batch.planned_selling_price = str(calculation_result.planned_selling_price) if calculation_result.planned_selling_price is not None else None
    batch.projected_profit = str(calculation_result.projected_profit) if calculation_result.projected_profit is not None else None
    batch.profit_margin_pct = str(calculation_result.profit_margin_pct) if calculation_result.profit_margin_pct is not None else None

    db.commit()
    db.refresh(batch)
    return batch


def delete_batch_record(db: Session, batch_id: str) -> bool:
    """Delete a saved batch record."""
    batch = get_batch_record(db, batch_id)
    if not batch:
        return False
    db.delete(batch)
    db.commit()
    return True

