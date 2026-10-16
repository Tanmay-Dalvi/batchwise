"""SQLAlchemy ORM models for recipes, ingredients, and batch costing history."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def generate_uuid() -> str:
    """Generate a stable UUID string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Generate current UTC datetime."""
    return datetime.now(timezone.utc)


class Recipe(Base):
    """Reusable product recipe template with default ingredients and overheads."""
    __tablename__ = "recipes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    yield_unit = Column(String(50), nullable=False, default="packets")

    # Default overhead estimates stored as Decimal strings (e.g. "50.00")
    default_packaging_cost = Column(String(32), nullable=False, default="0.00")
    default_labour_cost = Column(String(32), nullable=False, default="0.00")
    default_fuel_cost = Column(String(32), nullable=False, default="0.00")
    default_delivery_cost = Column(String(32), nullable=False, default="0.00")
    default_other_expenses = Column(String(32), nullable=False, default="0.00")

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.id",
    )
    batches = relationship(
        "BatchRecord",
        back_populates="recipe",
    )


class RecipeIngredient(Base):
    """Ingredient item belonging to a recipe template."""
    __tablename__ = "recipe_ingredients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recipe_id = Column(String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Stored as Decimal strings to preserve exact user inputs
    recipe_quantity = Column(String(32), nullable=False)
    recipe_unit = Column(String(32), nullable=False)
    purchase_quantity = Column(String(32), nullable=False)
    purchase_unit = Column(String(32), nullable=False)
    purchase_price = Column(String(32), nullable=False)

    recipe = relationship("Recipe", back_populates="ingredients")


class BatchRecord(Base):
    """An immutable or editable production batch run with its complete costing snapshot."""
    __tablename__ = "batch_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recipe_id = Column(String(36), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_name = Column(String(255), nullable=False, index=True)
    notes = Column(Text, nullable=True)

    # Serialized snapshots of calculation input and deterministic result
    calculation_input_json = Column(Text, nullable=False)
    calculation_result_json = Column(Text, nullable=False)

    # Indexed query fields for fast dashboard list queries
    total_batch_cost = Column(String(32), nullable=False)
    sellable_quantity = Column(String(32), nullable=False)
    unit_name = Column(String(50), nullable=False, default="packets")
    cost_per_sellable_unit = Column(String(32), nullable=False)
    planned_selling_price = Column(String(32), nullable=True)
    projected_profit = Column(String(32), nullable=True)
    profit_margin_pct = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    recipe = relationship("Recipe", back_populates="batches")


Index("idx_batch_created_at", BatchRecord.created_at.desc())
