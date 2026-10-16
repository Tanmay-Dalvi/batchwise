"""Tests for recipe CRUD endpoints."""

from fastapi import status


def test_recipe_lifecycle_crud(client, sample_recipe_payload):
    """Test full CRUD lifecycle for a recipe template."""
    # 1. Create Recipe
    create_resp = client.post("/api/v1/recipes", json=sample_recipe_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED
    created = create_resp.json()
    recipe_id = created["id"]
    assert created["name"] == "Traditional Rava Ladoo"
    assert created["yield_unit"] == "pieces"
    assert len(created["ingredients"]) == 3
    ing_map = {i["name"]: i for i in created["ingredients"]}
    assert "Rava (Semolina)" in ing_map
    assert ing_map["Rava (Semolina)"]["recipe_quantity"] == "1000"

    # 2. List Recipes
    list_resp = client.get("/api/v1/recipes")
    assert list_resp.status_code == status.HTTP_200_OK
    recipes = list_resp.json()
    assert len(recipes) >= 1
    assert any(r["id"] == recipe_id for r in recipes)

    # 3. Retrieve Recipe by ID
    get_resp = client.get(f"/api/v1/recipes/{recipe_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    fetched = get_resp.json()
    assert fetched["id"] == recipe_id
    assert fetched["name"] == "Traditional Rava Ladoo"

    # 4. Update Recipe
    update_payload = {
        "name": "Traditional Rava Ladoo (Diwali Special)",
        "default_packaging_cost": "35.00",
        "ingredients": [
            {
                "name": "Rava (Semolina)",
                "recipe_quantity": "1200",
                "recipe_unit": "g",
                "purchase_quantity": "1.5",
                "purchase_unit": "kg",
                "purchase_price": "90.00",
            }
        ],
    }
    update_resp = client.put(f"/api/v1/recipes/{recipe_id}", json=update_payload)
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["name"] == "Traditional Rava Ladoo (Diwali Special)"
    assert updated["default_packaging_cost"] == "35.00"
    assert len(updated["ingredients"]) == 1
    assert updated["ingredients"][0]["recipe_quantity"] == "1200"

    # 5. Delete Recipe
    del_resp = client.delete(f"/api/v1/recipes/{recipe_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # 6. Verify 404 after deletion
    get_again = client.get(f"/api/v1/recipes/{recipe_id}")
    assert get_again.status_code == status.HTTP_404_NOT_FOUND


def test_recipe_not_found_handling(client):
    """Operations on non-existent recipe IDs return HTTP 404."""
    non_existent_id = "non-existent-uuid-1234"
    assert client.get(f"/api/v1/recipes/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert client.put(f"/api/v1/recipes/{non_existent_id}", json={"name": "New"}).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/recipes/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND


def test_recipe_partial_update_overhead_fields(client, sample_recipe_payload):
    """Update individual overhead fields and description on an existing recipe."""
    create_resp = client.post("/api/v1/recipes", json=sample_recipe_payload)
    recipe_id = create_resp.json()["id"]

    update_payload = {
        "description": "Updated festive description",
        "yield_unit": "boxes",
        "default_labour_cost": "150.00",
        "default_fuel_cost": "45.00",
        "default_delivery_cost": "20.00",
        "default_other_expenses": "15.00",
    }
    update_resp = client.put(f"/api/v1/recipes/{recipe_id}", json=update_payload)
    assert update_resp.status_code == status.HTTP_200_OK
    data = update_resp.json()
    assert data["description"] == "Updated festive description"
    assert data["yield_unit"] == "boxes"
    assert data["default_labour_cost"] == "150.00"
    assert data["default_fuel_cost"] == "45.00"
    assert data["default_delivery_cost"] == "20.00"
    assert data["default_other_expenses"] == "15.00"

