"""AI extraction service connecting to local Ollama (Gemma 3 1B) with deterministic post-processing."""

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


async def parse_costing_note(
    note: str,
    ollama_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
) -> ParseNoteResponse:
    """
    Parse a natural-language costing note into a structured candidate batch extraction.
    
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

    base_url = (ollama_url or settings.OLLAMA_BASE_URL).rstrip("/")
    model_name = model or settings.OLLAMA_MODEL
    timeout = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    prompt = build_extraction_prompt(cleaned_note)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
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
        )
    except httpx.HTTPError as e:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=f"HTTP communication error with Ollama: {str(e)}. Manual entry is available.",
            model_used=model_name,
        )

    if resp.status_code != 200:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message=f"Ollama returned HTTP error {resp.status_code}: {resp.text}. Manual costing is available.",
            model_used=model_name,
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
        )

    raw_dict = _extract_json_payload(raw_llm_text)
    if raw_dict is None:
        return ParseNoteResponse(
            success=False,
            status="error",
            error_message="The model generated malformed output that could not be parsed into JSON. Manual costing is ready.",
            model_used=model_name,
        )

    candidate = _post_process_candidate(raw_dict, cleaned_note)
    status_str = "success" if candidate.can_calculate else "partial"

    return ParseNoteResponse(
        success=True,
        status=status_str,
        candidate=candidate,
        model_used=model_name,
    )
