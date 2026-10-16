"""Recipe template persistence endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.crud import (
    create_recipe,
    delete_recipe,
    get_recipe,
    list_recipes,
    update_recipe,
)
from app.db.database import get_db
from app.schemas.records import RecipeCreate, RecipeResponse, RecipeUpdate

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe_endpoint(
    recipe_in: RecipeCreate, db: Session = Depends(get_db)
) -> RecipeResponse:
    """Create a new recipe template."""
    recipe = create_recipe(db=db, recipe_in=recipe_in)
    return RecipeResponse.model_validate(recipe)


@router.get("", response_model=List[RecipeResponse])
def list_recipes_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[RecipeResponse]:
    """List saved recipes ordered by most recently updated."""
    recipes = list_recipes(db=db, skip=skip, limit=limit)
    return [RecipeResponse.model_validate(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe_endpoint(
    recipe_id: str, db: Session = Depends(get_db)
) -> RecipeResponse:
    """Retrieve a recipe template by ID."""
    recipe = get_recipe(db=db, recipe_id=recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe '{recipe_id}' not found.",
        )
    return RecipeResponse.model_validate(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe_endpoint(
    recipe_id: str, recipe_in: RecipeUpdate, db: Session = Depends(get_db)
) -> RecipeResponse:
    """Update a recipe template and its ingredients."""
    updated = update_recipe(db=db, recipe_id=recipe_id, recipe_in=recipe_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe '{recipe_id}' not found.",
        )
    return RecipeResponse.model_validate(updated)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe_endpoint(
    recipe_id: str, db: Session = Depends(get_db)
) -> None:
    """Delete a recipe template."""
    deleted = delete_recipe(db=db, recipe_id=recipe_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe '{recipe_id}' not found.",
        )

