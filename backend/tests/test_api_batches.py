"""Tests for batch costing record persistence and snapshot retrieval."""

from fastapi import status


def test_batch_record_lifecycle_crud(client, canonical_besan_payload):
    """Test creating, listing, retrieving, updating, and deleting a batch run."""
    batch_create_body = {
        "batch_costing": canonical_besan_payload,
        "notes": "Diwali festival preparation test batch",
    }

    # 1. Create Batch Record
    create_resp = client.post("/api/v1/batches", json=batch_create_body)
    assert create_resp.status_code == status.HTTP_201_CREATED
    batch = create_resp.json()
    batch_id = batch["id"]
    assert batch["batch_name"] == "Diwali Besan Sev Batch"
    assert batch["notes"] == "Diwali festival preparation test batch"
    assert batch["total_batch_cost"] == "860.00"
    assert batch["cost_per_sellable_unit"] == "11.47"
    assert batch["planned_selling_price"] == "25.00"
    assert batch["projected_profit"] == "1015.00"

    # Verify nested calculation input and deterministic result are preserved in snapshot
    assert batch["calculation_input"]["batch_name"] == "Diwali Besan Sev Batch"
    assert batch["calculation_result"]["cost_per_sellable_unit"] == "11.47"
    assert len(batch["calculation_result"]["audit_trail"]) >= 4

    # 2. List Batch Summaries
    list_resp = client.get("/api/v1/batches")
    assert list_resp.status_code == status.HTTP_200_OK
    summaries = list_resp.json()
    assert len(summaries) >= 1
    assert any(b["id"] == batch_id for b in summaries)

    # 3. Retrieve Single Batch by ID
    get_resp = client.get(f"/api/v1/batches/{batch_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    fetched = get_resp.json()
    assert fetched["id"] == batch_id
    assert fetched["cost_per_sellable_unit"] == "11.47"
    assert fetched["calculation_result"]["profit_margin_pct"] == "54.13"

    # 4. Update Batch Record (e.g. adjust selling price to ₹28.00)
    updated_costing = dict(canonical_besan_payload)
    updated_costing["planned_selling_price"] = "28.00"
    update_body = {
        "batch_costing": updated_costing,
        "notes": "Adjusted selling price to ₹28.00 per packet",
    }
    update_resp = client.put(f"/api/v1/batches/{batch_id}", json=update_body)
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["planned_selling_price"] == "28.00"
    # Revenue at 28: 75 * 28 = ₹2100. Profit = 2100 - 860 = ₹1240.
    assert updated["projected_profit"] == "1240.00"

    # 5. Delete Batch Record
    del_resp = client.delete(f"/api/v1/batches/{batch_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # 6. Verify 404 after deletion
    assert client.get(f"/api/v1/batches/{batch_id}").status_code == status.HTTP_404_NOT_FOUND


def test_batch_not_found_handling(client, canonical_besan_payload):
    """Operations on non-existent batch IDs return HTTP 404."""
    non_existent_id = "missing-batch-id-5678"
    assert client.get(f"/api/v1/batches/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/batches/{non_existent_id}").status_code == status.HTTP_404_NOT_FOUND

    update_body = {"batch_costing": canonical_besan_payload}
    assert client.put(f"/api/v1/batches/{non_existent_id}", json=update_body).status_code == status.HTTP_404_NOT_FOUND


def test_batch_list_filter_by_recipe_id(client, canonical_besan_payload, sample_recipe_payload):
    """Verify listing batch records filtered by recipe_id query parameter."""
    # Create recipe
    recipe_resp = client.post("/api/v1/recipes", json=sample_recipe_payload)
    recipe_id = recipe_resp.json()["id"]

    # Create batch linked to recipe
    batch_payload = {
        "batch_costing": canonical_besan_payload,
        "recipe_id": recipe_id,
        "notes": "Linked to recipe",
    }
    client.post("/api/v1/batches", json=batch_payload)

    # Create unlinked batch
    client.post("/api/v1/batches", json={"batch_costing": canonical_besan_payload})

    # Query filtered by recipe_id
    resp = client.get(f"/api/v1/batches?recipe_id={recipe_id}")
    assert resp.status_code == status.HTTP_200_OK
    results = resp.json()
    assert len(results) == 1
    assert results[0]["recipe_id"] == recipe_id

