"""Shared pytest fixtures for FastAPI test client and isolated test database."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import create_application


@pytest.fixture(scope="function")
def test_db_engine():
    """Create an isolated in-memory SQLite engine with StaticPool for the test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Provide an isolated database session per test function."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, future=True)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a FastAPI TestClient configured to use the isolated test database session."""
    app = create_application()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def canonical_besan_payload():
    """Canonical test case payload: 5 kg besan cost 600, oil 180, packaging 80, 75 packets, sold each for 25."""
    return {
        "batch_name": "Diwali Besan Sev Batch",
        "ingredients": [
            {
                "name": "Besan (Gram Flour)",
                "recipe_quantity": "5",
                "recipe_unit": "kg",
                "purchase_quantity": "5",
                "purchase_unit": "kg",
                "purchase_price": "600.00",
            },
            {
                "name": "Cooking Oil",
                "recipe_quantity": "1",
                "recipe_unit": "l",
                "purchase_quantity": "1",
                "purchase_unit": "l",
                "purchase_price": "180.00",
            },
        ],
        "packaging_cost": "80.00",
        "labour_cost": "0.00",
        "fuel_cost": "0.00",
        "delivery_cost": "0.00",
        "other_expenses": "0.00",
        "direct_wastage_expense": "0.00",
        "batch_yield": {
            "sellable_quantity": "75",
            "unit_name": "packets",
        },
        "planned_selling_price": "25.00",
        "target_margin_pct": "30.00",
    }


@pytest.fixture
def sample_recipe_payload():
    """Sample recipe template payload."""
    return {
        "name": "Traditional Rava Ladoo",
        "description": "Festive semolina ladoos with pure ghee and cardamom",
        "yield_unit": "pieces",
        "default_packaging_cost": "25.00",
        "default_labour_cost": "100.00",
        "default_fuel_cost": "30.00",
        "default_delivery_cost": "0.00",
        "default_other_expenses": "10.00",
        "ingredients": [
            {
                "name": "Rava (Semolina)",
                "recipe_quantity": "1000",
                "recipe_unit": "g",
                "purchase_quantity": "1",
                "purchase_unit": "kg",
                "purchase_price": "60.00",
            },
            {
                "name": "Sugar",
                "recipe_quantity": "800",
                "recipe_unit": "g",
                "purchase_quantity": "1",
                "purchase_unit": "kg",
                "purchase_price": "45.00",
            },
            {
                "name": "Pure Ghee",
                "recipe_quantity": "250",
                "recipe_unit": "ml",
                "purchase_quantity": "1",
                "purchase_unit": "l",
                "purchase_price": "700.00",
            },
        ],
    }

