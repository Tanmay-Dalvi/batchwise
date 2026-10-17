"""AI extraction service connecting to local Ollama (Gemma 3 1B) or hosted Google Gemini with deterministic post-processing."""

import json
import re
from typing import Any, Dict, List, Optional
import httpx

from app.ai.prompts import build_extraction_prompt
from app.ai.schemas import (
    AmbiguityFlag,
    CandidateBatchExtraction,
    CandidateIngredient,
    ParseNoteResponse,
)
from app.calculator.units import normalize_unit
from app.config import settings

# Regex to strip currency indicators
_CURRENCY_STRIP_RE = re.compile(r"(?:rupees?|rs\.?|₹|inr)", re.IGNORECASE)

# Regex to separate numeric quantity from trailing unit (e.g. "5kg" -> "5", "kg")
_QTY_UNIT_RE = re.compile(r"^([\d.]+)\s*([a-zA-Z]+)?$")


def _clean_number_string(val: Optional[Any]) -> Optional[str]:
    """Clean a currency or quantity string into clean Decimal string."""
    if val is None:
        return None
    raw = str(val).strip()
    cleaned = _CURRENCY_STRIP_RE.sub("", raw).strip()
    match = re.search(r"[\d.]+", cleaned)
    if match:
        try:
            # Validate float/decimal parsability
            float(match.group(0))
            return match.group(0)
        except ValueError:
            return None
    return None


def _extract_json_payload(response_text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON object from raw LLM response text."""
    if not response_text or not response_text.strip():
        return None

    cleaned = response_text.strip()

    # If wrapped in markdown code blocks, extract inner content
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if code_block_match:
        cleaned = code_block_match.group(1).strip()
    else:
        # Locate outermost braces
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _post_process_candidate(raw_dict: Dict[str, Any], raw_note: str) -> CandidateBatchExtraction:
    """
    Deterministic rule-based post-processor and ambiguity detector.
    
    Guarantees:
    - Never invents numbers
    - Strips currency and unit noise
    - Flags ambiguous quantities or prices
    - Ensures calculator is only enabled when all required fields are validated
    """
    ingredients: List[CandidateIngredient] = []
    missing_fields: List[str] = []
    ambiguities: List[AmbiguityFlag] = []

    # Process ingredients
    raw_ingredients = raw_dict.get("ingredients")
    if isinstance(raw_ingredients, list):
        for item in raw_ingredients:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue

            raw_qty = item.get("recipe_quantity")
            raw_unit = item.get("recipe_unit")
            raw_price = item.get("purchase_price")
            is_ambiguous = bool(item.get("is_ambiguous", False))
            ambiguity_reason = item.get("ambiguity_reason")

            # Parse quantity and unit if combined (e.g. "5 kg")
            clean_qty = _clean_number_string(raw_qty)
            clean_unit = str(raw_unit).strip().lower() if raw_unit else None

            if raw_qty and not clean_unit:
                unit_match = _QTY_UNIT_RE.match(str(raw_qty).strip())
                if unit_match and unit_match.group(2):
                    clean_qty = unit_match.group(1)
                    clean_unit = unit_match.group(2).lower()

            clean_price = _clean_number_string(raw_price)

            # Check for ambiguity in quantity or price
            if clean_price is None and clean_qty is None:
                is_ambiguous = True
                ambiguity_reason = ambiguity_reason or f"Missing both quantity and price for '{name}'."
                ambiguities.append(
                    AmbiguityFlag(
                        field_name=f"{name}_details",
                        raw_text=name,
                        question=f"What quantity and price was paid for {name}?",
                        options=[f"1 kg {name}", f"1 packet {name}", "Enter manually"],
                    )
                )
            elif clean_qty is None and clean_price is not None:
                is_ambiguous = True
                ambiguity_reason = ambiguity_reason or f"Price ₹{clean_price} specified, but quantity is missing."
                missing_fields.append(f"{name}_quantity")
                ambiguities.append(
                    AmbiguityFlag(
                        field_name=f"{name}_quantity",
                        raw_text=f"{name} ₹{clean_price}",
                        question=f"What quantity of {name} was used or bought for ₹{clean_price}?",
                        options=["1 kg", "1 liter", "1 packet", "500 g"],
                    )
                )
            elif clean_price is None and clean_qty is not None:
                is_ambiguous = True
                ambiguity_reason = ambiguity_reason or f"Quantity {clean_qty} {clean_unit or ''} specified, but price is missing."
                missing_fields.append(f"{name}_price")
                ambiguities.append(
                    AmbiguityFlag(
                        field_name=f"{name}_price",
                        raw_text=f"{clean_qty} {clean_unit or ''} {name}".strip(),
                        question=f"What was the purchase price for {clean_qty} {clean_unit or ''} of {name}?",
                        options=["Enter price in ₹"],
                    )
                )
            elif clean_price is not None and clean_qty is not None and clean_unit is not None:
                # Fully resolved ingredient
                is_ambiguous = False
                ambiguity_reason = None

            # Validate unit if present
            if clean_unit:
                try:
                    normalize_unit(clean_unit)
                except Exception:
                    is_ambiguous = True
                    ambiguity_reason = (ambiguity_reason or "") + f" Unrecognized unit '{clean_unit}'."

            ingredients.append(
                CandidateIngredient(
                    name=name,
                    recipe_quantity=clean_qty,
                    recipe_unit=clean_unit,
                    purchase_price=clean_price,
                    is_ambiguous=is_ambiguous,
                    ambiguity_reason=ambiguity_reason,
                )
            )

    # Process overheads
    pkg_cost = _clean_number_string(raw_dict.get("packaging_cost"))
    labour_cost = _clean_number_string(raw_dict.get("labour_cost"))
    fuel_cost = _clean_number_string(raw_dict.get("fuel_cost"))
    delivery_cost = _clean_number_string(raw_dict.get("delivery_cost"))
    other_cost = _clean_number_string(raw_dict.get("other_expenses"))

    # Process yield and price
    sellable_qty = _clean_number_string(raw_dict.get("sellable_quantity"))
    yield_unit = str(raw_dict.get("yield_unit_name") or "").strip() or None
    planned_price = _clean_number_string(raw_dict.get("planned_selling_price"))

    # Regex backup for yield if omitted by small model
    if sellable_qty is None:
        yield_match = re.search(r"(\d+)\s*(packets?|pkts?|pieces?|boxes?|units?|items?|laddus?|cookies?)", raw_note, re.IGNORECASE)
        if yield_match:
            sellable_qty = yield_match.group(1)
            yield_unit = yield_unit or yield_match.group(2).lower()

    # Regex backup for packaging if omitted
    if pkg_cost is None:
        pkg_match = re.search(r"(?:packaging|packing)\s*(?:cost)?\s*[:=]?\s*(\d+)", raw_note, re.IGNORECASE)
        if pkg_match:
            pkg_cost = pkg_match.group(1)

    # Regex backup for selling price if omitted
    if planned_price is None:
        price_match = re.search(r"(?:sold|selling|price|sale)\s*(?:each|for|at)?\s*(?:for|at)?\s*(?:rs\.?|₹)?\s*(\d+)", raw_note, re.IGNORECASE)
        if price_match:
            planned_price = price_match.group(1)

    # Missing fields audit
    if not ingredients:
        missing_fields.append("ingredients")
    if not sellable_qty:
        missing_fields.append("sellable_quantity")
        ambiguities.append(
            AmbiguityFlag(
                field_name="sellable_quantity",
                raw_text=raw_note,
                question="How many sellable packets or units did this batch produce?",
                options=["Enter quantity"],
            )
        )
    if not planned_price:
        missing_fields.append("planned_selling_price")

    # Assess if batch is ready for immediate calculation
    has_valid_ingredients = len(ingredients) > 0 and all(
        ing.recipe_quantity and ing.purchase_price and not ing.is_ambiguous for ing in ingredients
    )
    has_valid_yield = sellable_qty is not None and int(float(sellable_qty)) > 0
    can_calculate = has_valid_ingredients and has_valid_yield and len(ambiguities) == 0

    confidence_parts = []
    if ingredients:
        confidence_parts.append(f"{len(ingredients)} ingredient(s)")
    if pkg_cost:
        confidence_parts.append(f"packaging (₹{pkg_cost})")
    if sellable_qty:
        confidence_parts.append(f"yield ({sellable_qty} {yield_unit or 'units'})")
    if planned_price:
        confidence_parts.append(f"selling price (₹{planned_price})")

    summary = "Extracted " + (", ".join(confidence_parts) if confidence_parts else "partial information")
    if ambiguities:
        summary += f". {len(ambiguities)} item(s) require confirmation."
    elif can_calculate:
        summary += ". Ready for batch calculation."

    batch_name = str(raw_dict.get("batch_name") or "").strip() or None
    if not batch_name and ingredients:
        batch_name = f"{ingredients[0].name.title()} Batch"

    return CandidateBatchExtraction(
        raw_note=raw_note,
        batch_name=batch_name,
        ingredients=ingredients,
        packaging_cost=pkg_cost,
        labour_cost=labour_cost,
        fuel_cost=fuel_cost,
        delivery_cost=delivery_cost,
        other_expenses=other_cost,
        sellable_quantity=sellable_qty,
        yield_unit_name=yield_unit or "packets",
        planned_selling_price=planned_price,
        missing_fields=missing_fields,
        ambiguities=ambiguities,
        confidence_summary=summary,
        can_calculate=can_calculate,
    )


async def _discover_available_gemini_models(
    api_key: str,
    client: httpx.AsyncClient,
) -> List[str]:
    """
    Query Google Generative Language API ListModels endpoint to discover
    all active, supported models for this API key.
    """
    try:
        resp = await client.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": api_key},
            headers={"x-goog-api-key": api_key},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        models = data.get("models", [])

        candidates: List[str] = []
        for m in models:
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                name = m.get("name", "")
                clean = name.removeprefix("models/").strip()
                if clean:
                    candidates.append(clean)

        return candidates
    except Exception:
        return []


async def _call_gemini_api(
    prompt: str,
    api_key: str,
    model_name: str,
    timeout: float,
    cleaned_note: str,
) -> ParseNoteResponse:
    """
    Call Google Gemini generateContent REST API with structured JSON output mode.

    Guarantees:
    - Never leaks the API key in logs or error messages.
    - Handles model deprecation (404) with automatic active model discovery.
    - Handles rate limits (429), auth failures (401/403), network timeouts, and model errors gracefully.
    - Routes the response into deterministic post-processing.
    """
    clean_model = model_name.strip()
    if clean_model.startswith("models/"):
        clean_model = clean_model[len("models/"):].strip()

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    params = {"key": api_key}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent"
            resp = await client.post(url, headers=headers, params=params, json=payload)

            # If 404 (e.g. deprecated model like gemini-1.5-flash), attempt automatic fallback across active candidate models
            if resp.status_code == 404:
                discovered_models = await _discover_available_gemini_models(api_key, client)
                # Build prioritised candidate list, explicitly excluding clean_model that just failed
                fallback_pool = (
                    ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro", "gemini-flash"]
                    + [m for m in discovered_models if "flash" in m.lower()]
                    + discovered_models
                )
                seen = {clean_model}
                unique_fallbacks = []
                for m in fallback_pool:
                    if m not in seen:
                        seen.add(m)
                        unique_fallbacks.append(m)

                for candidate in unique_fallbacks:
                    fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent"
                    fallback_resp = await client.post(fallback_url, headers=headers, params=params, json=payload)
                    if fallback_resp.status_code == 200:
                        resp = fallback_resp
                        clean_model = candidate
                        break

    except httpx.ConnectError:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                "Unable to connect to Google Gemini API. Please check your internet connection. "
                "Manual batch costing remains 100% available."
            ),
            model_used=clean_model,
            provider_used="gemini",
        )
    except httpx.TimeoutException:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                f"Google Gemini model '{clean_model}' timed out after {timeout}s. "
                "Manual recipe and batch costing is ready."
            ),
            model_used=clean_model,
            provider_used="gemini",
        )
    except httpx.HTTPError as e:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=f"Network error communicating with Google Gemini: {type(e).__name__}. Manual entry is available.",
            model_used=clean_model,
            provider_used="gemini",
        )

    if resp.status_code == 429:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                "Google Gemini API rate limit or quota exceeded (HTTP 429). "
                "Please wait a moment and retry, or enter batch costs manually."
            ),
            model_used=clean_model,
            provider_used="gemini",
        )

    if resp.status_code in (401, 403):
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                "Google Gemini API authorization failed (HTTP 403/401). "
                "Please verify that your GEMINI_API_KEY is valid and has Gemini API enabled in Google AI Studio. "
                "Manual batch costing is ready."
            ),
            model_used=clean_model,
            provider_used="gemini",
        )

    if resp.status_code == 404:
        google_detail = ""
        try:
            google_detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            pass
        detail_suffix = f": {google_detail}" if google_detail else ""
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                f"Google Gemini model '{clean_model}' was not found (HTTP 404){detail_suffix}. "
                "Please set BATCHWISE_GEMINI_MODEL=gemini-2.5-flash in your environment. Manual costing is ready."
            ),
            model_used=clean_model,
            provider_used="gemini",
        )

    if resp.status_code != 200:
        google_detail = ""
        try:
            google_detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            pass
        detail_suffix = f": {google_detail}" if google_detail else ""
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=f"Google Gemini returned HTTP error {resp.status_code}{detail_suffix}. Manual costing is available.",
            model_used=clean_model,
            provider_used="gemini",
        )

    try:
        response_body = resp.json()
        candidates = response_body.get("candidates", [])
        if not candidates:
            return ParseNoteResponse(
                success=False,
                status="error",
                error_message="Google Gemini returned no candidate content for this note. Manual costing is ready.",
                model_used=clean_model,
                provider_used="gemini",
            )
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or not parts[0].get("text"):
            return ParseNoteResponse(
                success=False,
                status="error",
                error_message="Google Gemini response contained empty content parts. Manual costing is ready.",
                model_used=clean_model,
                provider_used="gemini",
            )
        raw_llm_text = parts[0]["text"]
    except Exception:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message="Google Gemini returned an unexpected response structure. Manual costing is ready.",
            model_used=clean_model,
            provider_used="gemini",
        )

    raw_dict = _extract_json_payload(raw_llm_text)
    if raw_dict is None:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message="The model generated malformed output that could not be parsed into JSON. Manual costing is ready.",
            model_used=clean_model,
            provider_used="gemini",
        )

    candidate = _post_process_candidate(raw_dict, cleaned_note)
    status_str = "success" if candidate.can_calculate else "partial"

    return ParseNoteResponse(
        success=True,
        status=status_str,
        candidate=candidate,
        model_used=clean_model,
        provider_used="gemini",
    )


async def _call_ollama_api(
    prompt: str,
    base_url: str,
    model_name: str,
    timeout: float,
    cleaned_note: str,
) -> ParseNoteResponse:
    """
    Call local Ollama /api/generate endpoint with JSON mode.
    """
    clean_url = f"{base_url.rstrip('/')}/api/generate"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                clean_url,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                },
            )
    except httpx.ConnectError:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                f"Local Ollama service is not reachable at {base_url}. "
                "Ensure Ollama is running (`ollama serve`). Manual batch costing remains fully available."
            ),
            model_used=model_name,
            provider_used="ollama",
        )
    except httpx.TimeoutException:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=(
                f"Local Ollama model '{model_name}' timed out after {timeout}s. "
                "Manual recipe and batch costing is ready."
            ),
            model_used=model_name,
            provider_used="ollama",
        )
    except httpx.HTTPError as e:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=f"HTTP communication error with Ollama: {str(e)}. Manual entry is available.",
            model_used=model_name,
            provider_used="ollama",
        )

    if resp.status_code != 200:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=f"Ollama returned HTTP error {resp.status_code}: {resp.text}. Manual costing is available.",
            model_used=model_name,
            provider_used="ollama",
        )

    try:
        response_body = resp.json()
        raw_llm_text = response_body.get("response", "")
    except Exception:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message="Ollama returned an unexpected non-JSON response payload.",
            model_used=model_name,
            provider_used="ollama",
        )

    raw_dict = _extract_json_payload(raw_llm_text)
    if raw_dict is None:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message="The model generated malformed output that could not be parsed into JSON. Manual costing is ready.",
            model_used=model_name,
            provider_used="ollama",
        )

    candidate = _post_process_candidate(raw_dict, cleaned_note)
    status_str = "success" if candidate.can_calculate else "partial"

    return ParseNoteResponse(
        success=True,
        status=status_str,
        candidate=candidate,
        model_used=model_name,
        provider_used="ollama",
    )


async def parse_costing_note(
    note: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    ollama_url: Optional[str] = None,
) -> ParseNoteResponse:
    """
    Parse a natural-language costing note into a structured candidate batch extraction.

    Supports:
    - Hosted Google Gemini API (gemini-1.5-flash / gemini-2.0-flash)
    - Local Ollama (Gemma 3 1B)
    - Automatic provider fallback (uses Gemini if API key configured, otherwise Ollama)

    Guarantees:
    - Never crashes on timeouts, connection failures, or malformed LLM responses
    - Strictly delegates all calculations to the deterministic financial engine
    - Reports ambiguities explicitly rather than fabricating data
    """
    cleaned_note = note.strip()
    if not cleaned_note:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message="Empty note provided. Please enter recipe ingredients, expenses, or yield.",
        )

    active_provider = (provider or settings.get_effective_ai_provider()).lower().strip()
    prompt = build_extraction_prompt(cleaned_note)

    if active_provider == "gemini":
        gemini_key = (api_key or settings.GEMINI_API_KEY).strip()
        model_name = model or settings.GEMINI_MODEL
        timeout = timeout_seconds or settings.GEMINI_TIMEOUT_SECONDS

        if not gemini_key:
            return ParseNoteResponse(
                success=False,
                status="error",
                error_message=(
                    "Google Gemini API key is not configured. "
                    "Set GEMINI_API_KEY environment variable in your deployment settings, "
                    "or configure BATCHWISE_AI_PROVIDER=ollama for local AI. Manual costing is always ready."
                ),
                model_used=model_name,
                provider_used="gemini",
            )

        return await _call_gemini_api(
            prompt=prompt,
            api_key=gemini_key,
            model_name=model_name,
            timeout=timeout,
            cleaned_note=cleaned_note,
        )

    # Local Ollama fallback
    base_url = ollama_url or settings.OLLAMA_BASE_URL
    model_name = model or settings.OLLAMA_MODEL
    timeout = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    return await _call_ollama_api(
        prompt=prompt,
        base_url=base_url,
        model_name=model_name,
        timeout=timeout,
        cleaned_note=cleaned_note,
    )


def get_ai_service_status() -> Dict[str, Any]:
    """Retrieve operational status and provider details for the AI note parser."""
    provider = settings.get_effective_ai_provider()
    if provider == "gemini":
        is_configured = bool(settings.GEMINI_API_KEY)
        return {
            "provider": "gemini",
            "model": settings.GEMINI_MODEL,
            "is_configured": is_configured,
            "description": (
                f"Google Gemini ({settings.GEMINI_MODEL}) Hosted Cloud AI"
                if is_configured
                else f"Google Gemini ({settings.GEMINI_MODEL}) - API key not set"
            ),
        }
    else:
        return {
            "provider": "ollama",
            "model": settings.OLLAMA_MODEL,
            "is_configured": True,
            "description": f"Gemma 3 ({settings.OLLAMA_MODEL}) on Local Ollama (Private)",
        }
