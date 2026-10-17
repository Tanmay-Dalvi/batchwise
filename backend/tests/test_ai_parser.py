"""Tests for AI note parsing, ambiguity detection, and failure resilience with mocked Ollama."""

import json
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi import status

from app.ai.parser import (
    _clean_number_string,
    _extract_json_payload,
    parse_costing_note,
)
from app.ai.schemas import ParseNoteResponse


# --- Helper unit tests ---

def test_clean_number_string_variations():
    """Verify currency cleaning and number extraction."""
    assert _clean_number_string("600 rupees") == "600"
    assert _clean_number_string("₹180.50") == "180.50"
    assert _clean_number_string("Rs. 80") == "80"
    assert _clean_number_string("Rs 25 each") == "25"
    assert _clean_number_string("5 kg") == "5"
    assert _clean_number_string(None) is None
    assert _clean_number_string("no numbers here") is None


def test_extract_json_payload_markdown_blocks():
    """Verify JSON extraction from markdown code fences and noisy LLM responses."""
    raw_markdown = "```json\n{\"batch_name\": \"Besan Sev\", \"ingredients\": []}\n```"
    data = _extract_json_payload(raw_markdown)
    assert data is not None
    assert data["batch_name"] == "Besan Sev"

    noisy_text = "Here is the extracted data:\n{\"packaging_cost\": \"80\"}\nHope this helps!"
    data2 = _extract_json_payload(noisy_text)
    assert data2 is not None
    assert data2["packaging_cost"] == "80"

    assert _extract_json_payload("") is None
    assert _extract_json_payload("not json at all") is None


# --- Note Parsing Tests with Mocked Ollama ---

@pytest.mark.anyio
async def test_parse_note_example_a_canonical():
    """
    Test Note A:
    '5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, selling price 25 each.'
    """
    mock_llm_json = {
        "batch_name": "Besan Batch",
        "ingredients": [
            {"name": "besan", "recipe_quantity": "5", "recipe_unit": "kg", "purchase_price": "600", "is_ambiguous": False},
            {"name": "oil", "recipe_quantity": None, "recipe_unit": None, "purchase_price": "180", "is_ambiguous": True, "ambiguity_reason": "Price ₹180 extracted, but quantity and unit are not specified"},
        ],
        "packaging_cost": "80",
        "sellable_quantity": "75",
        "yield_unit_name": "packets",
        "planned_selling_price": "25",
    }

    mock_resp = httpx.Response(
        status_code=200,
        json={"response": json.dumps(mock_llm_json)},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await parse_costing_note(
            "5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, selling price 25 each."
        )

    assert result.success is True
    assert result.status == "partial"  # Partial because oil quantity is missing/ambiguous
    candidate = result.candidate
    assert candidate is not None
    assert candidate.batch_name == "Besan Batch"
    assert len(candidate.ingredients) == 2

    # Besan is fully resolved
    besan = next(i for i in candidate.ingredients if i.name == "besan")
    assert besan.recipe_quantity == "5"
    assert besan.recipe_unit == "kg"
    assert besan.purchase_price == "600"
    assert besan.is_ambiguous is False

    # Oil is flagged ambiguous (missing quantity)
    oil = next(i for i in candidate.ingredients if i.name == "oil")
    assert oil.purchase_price == "180"
    assert oil.is_ambiguous is True

    assert candidate.packaging_cost == "80"
    assert candidate.sellable_quantity == "75"
    assert candidate.yield_unit_name == "packets"
    assert candidate.planned_selling_price == "25"
    assert len(candidate.ambiguities) >= 1
    assert candidate.can_calculate is False  # Cannot calculate until oil quantity is clarified


@pytest.mark.anyio
async def test_parse_note_example_b_missing_quantities():
    """
    Test Note B:
    'Besan 600, oil 180, 75 packets.'
    Missing quantities for both besan and oil.
    """
    mock_llm_json = {
        "batch_name": "Besan Batch",
        "ingredients": [
            {"name": "besan", "recipe_quantity": None, "recipe_unit": None, "purchase_price": "600", "is_ambiguous": True},
            {"name": "oil", "recipe_quantity": None, "recipe_unit": None, "purchase_price": "180", "is_ambiguous": True},
        ],
        "sellable_quantity": "75",
        "yield_unit_name": "packets",
    }

    mock_resp = httpx.Response(
        status_code=200,
        json={"response": json.dumps(mock_llm_json)},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note("Besan 600, oil 180, 75 packets.")

    assert result.success is True
    assert result.status == "partial"
    candidate = result.candidate
    assert candidate.sellable_quantity == "75"
    assert len(candidate.ambiguities) >= 2  # Ambiguities for besan and oil quantities
    assert candidate.can_calculate is False


@pytest.mark.anyio
async def test_parse_note_example_c_single_ambiguous_item():
    """
    Test Note C:
    'Oil 180.'
    Does 180 mean price ₹180 or quantity 180 ml? Requires clarification.
    """
    mock_llm_json = {
        "batch_name": None,
        "ingredients": [
            {"name": "oil", "recipe_quantity": None, "recipe_unit": None, "purchase_price": None, "is_ambiguous": True, "ambiguity_reason": "180 could be ₹180 price or 180 ml volume"}
        ],
        "sellable_quantity": None,
    }

    mock_resp = httpx.Response(
        status_code=200,
        json={"response": json.dumps(mock_llm_json)},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note("Oil 180.")

    assert result.success is True
    assert result.status == "partial"
    candidate = result.candidate
    assert len(candidate.ingredients) == 1
    assert candidate.ingredients[0].is_ambiguous is True
    assert "sellable_quantity" in candidate.missing_fields
    assert candidate.can_calculate is False


@pytest.mark.anyio
async def test_parse_note_example_d_yield_and_sales_only():
    """
    Test Note D:
    'Made 75 packets. Sold each for 25.'
    No ingredients or expenses entered.
    """
    mock_llm_json = {
        "batch_name": None,
        "ingredients": [],
        "sellable_quantity": "75",
        "yield_unit_name": "packets",
        "planned_selling_price": "25",
    }

    mock_resp = httpx.Response(
        status_code=200,
        json={"response": json.dumps(mock_llm_json)},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note("Made 75 packets. Sold each for 25.")

    assert result.success is True
    assert result.status == "partial"
    candidate = result.candidate
    assert candidate.sellable_quantity == "75"
    assert candidate.planned_selling_price == "25"
    assert "ingredients" in candidate.missing_fields
    assert candidate.can_calculate is False


@pytest.mark.anyio
async def test_parse_note_empty_input():
    """Empty note input returns structured error without contacting model."""
    result = await parse_costing_note("   ")
    assert result.success is False
    assert result.status == "error"
    assert "Empty note provided" in result.error_message


@pytest.mark.anyio
async def test_parse_note_ollama_unavailable():
    """Ollama connection refusal returns clean error indicating manual costing is available."""
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        result = await parse_costing_note("5 kg flour for 200")

    assert result.success is False
    assert result.status == "error"
    assert "Local Ollama service is not reachable" in result.error_message
    assert "Manual batch costing remains fully available" in result.error_message


@pytest.mark.anyio
async def test_parse_note_ollama_timeout():
    """Ollama timeout returns clean error without crashing."""
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Read timed out")
        result = await parse_costing_note("5 kg flour for 200")

    assert result.success is False
    assert result.status == "error"
    assert "timed out" in result.error_message
    assert "Manual recipe and batch costing is ready" in result.error_message


@pytest.mark.anyio
async def test_parse_note_malformed_model_json():
    """Malformed non-JSON output from LLM is handled safely."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"response": "I cannot parse this into JSON."},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note("flour 500")

    assert result.success is False
    assert result.status == "error"
    assert "malformed output" in result.error_message


@pytest.mark.anyio
async def test_parse_note_ollama_http_500():
    """Ollama internal server error returns clean error status."""
    mock_resp = httpx.Response(
        status_code=500,
        text="Internal Server Error in llama.cpp runner",
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note("flour 500")

    assert result.success is False
    assert result.status == "error"
    assert "HTTP error 500" in result.error_message


# --- API Endpoint Test ---

def test_api_parse_note_endpoint(client):
    """POST /api/v1/parse-note endpoint staging verification."""
    mock_llm_json = {
        "batch_name": "Rava Ladoo",
        "ingredients": [
            {"name": "rava", "recipe_quantity": "1", "recipe_unit": "kg", "purchase_price": "60", "is_ambiguous": False}
        ],
        "sellable_quantity": "40",
        "yield_unit_name": "pieces",
        "planned_selling_price": "10",
    }

    mock_resp = httpx.Response(
        status_code=200,
        json={"response": json.dumps(mock_llm_json)},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        # 1. Parse note
        resp = client.post("/api/v1/parse-note", json={"note": "1 kg rava 60 rs, made 40 pieces, sold for 10"})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["success"] is True
        assert data["candidate"]["batch_name"] == "Rava Ladoo"
        assert data["candidate"]["sellable_quantity"] == "40"
        assert data["candidate"]["can_calculate"] is True

        # 2. Verify NO database records were created by parsing
        recipes_resp = client.get("/api/v1/recipes")
        assert len(recipes_resp.json()) == 0
        batches_resp = client.get("/api/v1/batches")
        assert len(batches_resp.json()) == 0


def test_post_process_quantity_without_price():
    """Ingredient with quantity but missing purchase price flags ambiguity."""
    from app.ai.parser import _post_process_candidate

    raw_dict = {
        "ingredients": [
            {"name": "Sugar", "recipe_quantity": "5", "recipe_unit": "kg", "purchase_price": None}
        ]
    }
    cand = _post_process_candidate(raw_dict, "5 kg sugar")
    assert cand.ingredients[0].is_ambiguous is True
    assert "Sugar_price" in cand.missing_fields
    assert cand.can_calculate is False


def test_post_process_unrecognized_unit():
    """Unrecognized unit flags ambiguity on the ingredient."""
    from app.ai.parser import _post_process_candidate

    raw_dict = {
        "ingredients": [
            {"name": "Flour", "recipe_quantity": "3", "recipe_unit": "buckets", "purchase_price": "150"}
        ]
    }
    cand = _post_process_candidate(raw_dict, "3 buckets flour for 150")
    assert cand.ingredients[0].is_ambiguous is True
    assert "Unrecognized unit 'buckets'" in cand.ingredients[0].ambiguity_reason


def test_post_process_empty_or_malformed_ingredient_entries():
    """Non-dict or empty name items in ingredients list are ignored gracefully."""
    from app.ai.parser import _post_process_candidate

    raw_dict = {
        "ingredients": [
            "not a dict",
            {"name": ""},
            {"name": "Cardamom", "recipe_quantity": "50", "recipe_unit": "g", "purchase_price": "200"}
        ]
    }
    cand = _post_process_candidate(raw_dict, "50g cardamom 200")
    assert len(cand.ingredients) == 1
    assert cand.ingredients[0].name == "Cardamom"


@pytest.mark.anyio
async def test_parse_note_corrupted_response_body():
    """Ollama response body with unparsable JSON raises clean error."""
    mock_resp = httpx.Response(
        status_code=200,
        content=b"invalid raw bytes not json",
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note("flour 500")

    assert result.success is False
    assert result.status == "error"
    assert "unexpected non-JSON response payload" in result.error_message


def test_clean_number_string_nan_edge():
    """Single period or dot without digits returns None."""
    assert _clean_number_string(".") is None
    assert _clean_number_string("..") is None


# --- Google Gemini AI Unit Tests (Mocked) ---

@pytest.mark.anyio
async def test_parse_note_gemini_success():
    """Verify successful parsing with Google Gemini API using mock REST response."""
    mock_llm_json = {
        "batch_name": "Besan Batch",
        "ingredients": [
            {"name": "besan", "recipe_quantity": "5", "recipe_unit": "kg", "purchase_price": "600", "is_ambiguous": False},
            {"name": "oil", "recipe_quantity": "1", "recipe_unit": "l", "purchase_price": "180", "is_ambiguous": False},
        ],
        "packaging_cost": "80",
        "sellable_quantity": "75",
        "yield_unit_name": "packets",
        "planned_selling_price": "25",
    }
    gemini_resp_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(mock_llm_json)}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ]
    }
    mock_resp = httpx.Response(
        status_code=200,
        json=gemini_resp_payload,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note(
            "5 kg besan cost 600 rupees, 1 l oil 180, packaging 80, made 75 packets, selling price 25 each.",
            provider="gemini",
            api_key="test-api-key-12345",
        )

    assert result.success is True
    assert result.status == "success"
    assert result.provider_used == "gemini"
    assert result.model_used == "gemini-2.5-flash"
    assert result.candidate is not None
    assert result.candidate.batch_name == "Besan Batch"
    assert len(result.candidate.ingredients) == 2
    assert result.candidate.can_calculate is True


@pytest.mark.anyio
async def test_parse_note_gemini_rate_limit_429():
    """Verify Gemini HTTP 429 rate limit is handled gracefully with clear guidance."""
    mock_resp = httpx.Response(
        status_code=429,
        json={"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota)."}},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note(
            "5 kg besan 600",
            provider="gemini",
            api_key="test-api-key-12345",
        )

    assert result.success is False
    assert result.status == "error"
    assert result.provider_used == "gemini"
    assert "rate limit or quota exceeded" in result.error_message.lower()
    assert "manual" in result.error_message.lower()


@pytest.mark.anyio
async def test_parse_note_gemini_auth_failure_403():
    """Verify Gemini invalid API key (403/401) is handled with clear instructions."""
    mock_resp = httpx.Response(
        status_code=403,
        json={"error": {"code": 403, "message": "API key not valid. Please pass a valid API key."}},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note(
            "5 kg besan 600",
            provider="gemini",
            api_key="invalid-key",
        )

    assert result.success is False
    assert result.status == "error"
    assert result.provider_used == "gemini"
    assert "authorization failed" in result.error_message.lower()
    assert "GEMINI_API_KEY" in result.error_message


@pytest.mark.anyio
async def test_parse_note_gemini_timeout():
    """Verify Gemini request timeout returns clean error without crashing."""
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Read timed out")
        result = await parse_costing_note(
            "5 kg besan 600",
            provider="gemini",
            api_key="test-api-key",
            timeout_seconds=5.0,
        )

    assert result.success is False
    assert result.status == "error"
    assert result.provider_used == "gemini"
    assert "timed out after 5.0s" in result.error_message


@pytest.mark.anyio
async def test_parse_note_gemini_connect_error():
    """Verify network connection error to Gemini API is handled gracefully."""
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Failed to resolve host")
        result = await parse_costing_note(
            "5 kg besan 600",
            provider="gemini",
            api_key="test-api-key",
        )

    assert result.success is False
    assert result.status == "error"
    assert result.provider_used == "gemini"
    assert "Unable to connect to Google Gemini API" in result.error_message


@pytest.mark.anyio
async def test_parse_note_gemini_missing_key():
    """Requesting Gemini provider without an API key returns clean guidance."""
    result = await parse_costing_note(
        "5 kg besan 600",
        provider="gemini",
        api_key="",  # Empty key
    )
    assert result.success is False
    assert result.status == "error"
    assert "GEMINI_API_KEY" in result.error_message


@pytest.mark.anyio
async def test_parse_note_gemini_empty_parts():
    """Gemini response with empty parts returns safe error."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"candidates": [{"content": {"parts": []}}]},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await parse_costing_note(
            "5 kg besan 600",
            provider="gemini",
            api_key="test-api-key",
        )

    assert result.success is False
    assert result.status == "error"
    assert "empty content parts" in result.error_message


def test_effective_ai_provider_resolution(monkeypatch):
    """Verify Settings.get_effective_ai_provider behavior."""
    from app.config import settings

    # Explicit gemini
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    assert settings.get_effective_ai_provider() == "gemini"

    # Explicit ollama
    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    assert settings.get_effective_ai_provider() == "ollama"

    # Auto mode with key
    monkeypatch.setattr(settings, "AI_PROVIDER", "auto")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy-key")
    assert settings.get_effective_ai_provider() == "gemini"

    # Auto mode without key
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    assert settings.get_effective_ai_provider() == "ollama"


def test_api_parse_note_status_endpoint(client, monkeypatch):
    """GET /api/v1/parse-note/status returns active provider details."""
    from app.config import settings

    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "some-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

    resp = client.get("/api/v1/parse-note/status")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-2.5-flash"
    assert data["is_configured"] is True
    assert "Google Gemini" in data["description"]


@pytest.mark.anyio
async def test_parse_note_gemini_404_auto_discovery_fallback():
    """Verify when configured model returns 404, parser discovers active model and succeeds."""
    mock_llm_json = {
        "batch_name": "Sourdough Batch",
        "ingredients": [
            {"name": "flour", "recipe_quantity": "2", "recipe_unit": "kg", "purchase_price": "140", "is_ambiguous": False}
        ],
        "sellable_quantity": "8",
        "yield_unit_name": "loaves",
        "planned_selling_price": "90",
    }

    # 1. 404 on deprecated gemini-1.5-flash
    resp_404 = httpx.Response(
        status_code=404,
        json={"error": {"code": 404, "message": "models/gemini-1.5-flash is not found for API version v1beta"}},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"),
    )

    # 2. ListModels response discovering gemini-2.5-flash
    list_models_resp = httpx.Response(
        status_code=200,
        json={
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "supportedGenerationMethods": ["generateContent", "countTokens"],
                }
            ]
        },
        request=httpx.Request("GET", "https://generativelanguage.googleapis.com/v1beta/models"),
    )

    # 3. Success on discovered gemini-2.5-flash
    resp_success = httpx.Response(
        status_code=200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(mock_llm_json)}],
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"),
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get, \
         patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_get.return_value = list_models_resp
        mock_post.side_effect = [resp_404, resp_success]

        result = await parse_costing_note(
            "2 kg flour 140, baked 8 loaves, selling for 90 each",
            provider="gemini",
            api_key="valid-key",
            model="gemini-1.5-flash",
        )

    assert result.success is True
    assert result.status == "success"
    assert result.model_used == "gemini-2.5-flash"  # Auto-migrated to discovered model
    assert result.candidate is not None
    assert result.candidate.batch_name == "Sourdough Batch"


@pytest.mark.anyio
async def test_parse_note_gemini_404_no_fallback_gives_clear_guidance():
    """Verify 404 when no fallback is found outputs clear guidance and Google's message."""
    resp_404 = httpx.Response(
        status_code=404,
        json={"error": {"code": 404, "message": "Model not found"}},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/unknown-model:generateContent"),
    )
    list_models_empty = httpx.Response(
        status_code=200,
        json={"models": []},
        request=httpx.Request("GET", "https://generativelanguage.googleapis.com/v1beta/models"),
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get, \
         patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_get.return_value = list_models_empty
        mock_post.return_value = resp_404

        result = await parse_costing_note(
            "2 kg flour 140",
            provider="gemini",
            api_key="valid-key",
            model="unknown-model",
        )

    assert result.success is False
    assert result.status == "error"
    assert "HTTP 404" in result.error_message
    assert "BATCHWISE_GEMINI_MODEL=gemini-2.5-flash" in result.error_message

