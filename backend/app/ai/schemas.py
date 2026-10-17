"""Pydantic schemas for AI note extraction and candidate costing staging."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CandidateIngredient(BaseModel):
    """Candidate ingredient extracted from messy natural-language notes."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1)
    recipe_quantity: Optional[str] = None
    recipe_unit: Optional[str] = None
    purchase_quantity: Optional[str] = None
    purchase_unit: Optional[str] = None
    purchase_price: Optional[str] = None
    is_ambiguous: bool = False
    ambiguity_reason: Optional[str] = None


class AmbiguityFlag(BaseModel):
    """Specific missing or ambiguous field requiring seller clarification."""
    model_config = ConfigDict(extra="ignore")

    field_name: str
    raw_text: str
    question: str
    options: List[str] = Field(default_factory=list)


class CandidateBatchExtraction(BaseModel):
    """Candidate batch costing inputs extracted from text, staged for user review."""
    model_config = ConfigDict(extra="ignore")

    raw_note: str
    batch_name: Optional[str] = None
    ingredients: List[CandidateIngredient] = Field(default_factory=list)
    packaging_cost: Optional[str] = None
    labour_cost: Optional[str] = None
    fuel_cost: Optional[str] = None
    delivery_cost: Optional[str] = None
    other_expenses: Optional[str] = None
    sellable_quantity: Optional[str] = None
    yield_unit_name: Optional[str] = None
    planned_selling_price: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    ambiguities: List[AmbiguityFlag] = Field(default_factory=list)
    confidence_summary: str = ""
    can_calculate: bool = False


class ParseNoteRequest(BaseModel):
    """Incoming request to parse natural-language costing notes."""
    note: str = Field(..., min_length=1, max_length=5000, description="Raw seller note")


class ParseNoteResponse(BaseModel):
    """Response containing candidate extraction and status flags."""
    success: bool
    status: str = Field(..., description="'success', 'partial', or 'error'")
    candidate: Optional[CandidateBatchExtraction] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = Field(default=None, description="'gemini' or 'ollama'")


class AiStatusResponse(BaseModel):
    """Operational status and active provider configuration for AI note extraction."""
    provider: str = Field(..., description="'gemini' or 'ollama'")
    model: str = Field(..., description="Active model name")
    is_configured: bool = Field(..., description="True if provider is ready to process requests")
    description: str = Field(..., description="Human-friendly provider status description")

