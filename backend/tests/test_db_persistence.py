"""Test SQLite database isolation and persistence across simulated application restarts."""

import json
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.calculator.engine import calculate_batch
from app.calculator.models import BatchYieldInput, BatchCostingInput, IngredientInput
from app.db.crud import (
    create_batch_record,
    create_recipe,
    get_batch_record,
    get_recipe,
)
from app.db.database import Base, init_db
from app.schemas.records import RecipeCreate, RecipeIngredientCreate


def test_sqlite_persistence_across_restarts(tmp_path):
    """
    Simulate an application restart by writing to an on-disk SQLite file,
    disposing the engine, and reading back from a completely new engine instance.
    """
    db_file = tmp_path / "restart_test.db"
    db_url = f"sqlite:///{db_file}"

    # --- Phase A: Initial application run and persistence ---
    engine_1 = create_engine(db_url, future=True)
    init_db(engine_1)
    Session1 = sessionmaker(bind=engine_1, future=True)

    with Session1() as session1:
        # 1. Create a Recipe
        recipe_data = RecipeCreate(
            name="Poha Chivda",
            description="Crispy roasted poha mixture",
            yield_unit="packets",
            default_packaging_cost=Decimal("15.00"),
            ingredients=[
                RecipeIngredientCreate(
                    name="Poha (Flattened Rice)",
                    recipe_quantity=Decimal("1"),
                    recipe_unit="kg",
                    purchase_price=Decimal("50.00"),
                ),
                RecipeIngredientCreate(
                    name="Peanuts",
                    recipe_quantity=Decimal("200"),
                    recipe_unit="g",
                    purchase_quantity=Decimal("1"),
                    purchase_unit="kg",
                    purchase_price=Decimal("120.00"),
                ),
            ],
        )
        saved_recipe = create_recipe(session1, recipe_data)
        recipe_id = saved_recipe.id

        # 2. Create a BatchRecord
        batch_input = BatchCostingInput(
            batch_name="Poha Chivda Diwali Run #1",
            ingredients=[
                IngredientInput(
                    name="Poha",
                    recipe_quantity=Decimal("1"),
                    recipe_unit="kg",
                    purchase_price=Decimal("50.00"),
                )
            ],
            packaging_cost=Decimal("15.00"),
            batch_yield=BatchYieldInput(sellable_quantity=Decimal("10"), unit_name="packets"),
            planned_selling_price=Decimal("15.00"),
        )
        calc_result = calculate_batch(batch_input)
        saved_batch = create_batch_record(
            session1,
            batch_input=batch_input,
            calculation_result=calc_result,
            recipe_id=recipe_id,
            notes="Stored before restart",
        )
        batch_id = saved_batch.id

    # Dispose Engine 1 (Application Shutdown)
    engine_1.dispose()

    # --- Phase B: Application restarts, connecting to same SQLite file ---
    engine_2 = create_engine(db_url, future=True)
    Session2 = sessionmaker(bind=engine_2, future=True)

    with Session2() as session2:
        # Verify Recipe survived restart
        reloaded_recipe = get_recipe(session2, recipe_id)
        assert reloaded_recipe is not None
        assert reloaded_recipe.name == "Poha Chivda"
        assert reloaded_recipe.default_packaging_cost == "15.00"
        assert len(reloaded_recipe.ingredients) == 2
        ing_map = {i.name: i for i in reloaded_recipe.ingredients}
        assert "Poha (Flattened Rice)" in ing_map
        assert "Peanuts" in ing_map
        assert ing_map["Peanuts"].purchase_quantity == "1"

        # Verify Batch Record survived restart
        reloaded_batch = get_batch_record(session2, batch_id)
        assert reloaded_batch is not None
        assert reloaded_batch.batch_name == "Poha Chivda Diwali Run #1"
        assert reloaded_batch.recipe_id == recipe_id
        assert reloaded_batch.notes == "Stored before restart"
        assert reloaded_batch.total_batch_cost == "65.00"
        assert reloaded_batch.cost_per_sellable_unit == "6.50"
        assert reloaded_batch.projected_profit == "85.00"

        # Verify JSON snapshot survived intact
        input_data = json.loads(reloaded_batch.calculation_input_json)
        result_data = json.loads(reloaded_batch.calculation_result_json)
        assert input_data["batch_name"] == "Poha Chivda Diwali Run #1"
        assert result_data["cost_per_sellable_unit"] == "6.50"

    engine_2.dispose()


def test_get_db_generator():
    """Verify get_db dependency yields active Session and closes it upon exit."""
    from app.db.database import get_db

    gen = get_db()
    session = next(gen)
    assert session is not None
    assert session.is_active is True
    # Complete generator
    try:
        next(gen)
    except StopIteration:
        pass


def test_update_batch_record_not_found(db_session, canonical_besan_payload):
    """update_batch_record returns None when target batch does not exist."""
    from app.calculator.engine import calculate_batch
    from app.calculator.models import BatchCostingInput
    from app.db.crud import update_batch_record

    batch_input = BatchCostingInput.model_validate(canonical_besan_payload)
    calc_res = calculate_batch(batch_input)
    assert update_batch_record(db_session, "non-existent-batch-id", batch_input, calc_res) is None

