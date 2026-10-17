"""Endpoint for parsing messy natural-language costing notes into structured candidate inputs."""

from fastapi import APIRouter, status

from app.ai.parser import get_ai_service_status, parse_costing_note
from app.ai.schemas import AiStatusResponse, ParseNoteRequest, ParseNoteResponse

router = APIRouter(tags=["ai"])


@router.get(
    "/parse-note/status",
    response_model=AiStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current AI provider and model configuration status",
)
def get_parse_status_endpoint() -> AiStatusResponse:
    """
    Return active AI provider (hosted Google Gemini or local Ollama) and readiness status.
    """
    return AiStatusResponse(**get_ai_service_status())


@router.post(
    "/parse-note",
    response_model=ParseNoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract candidate costing fields from natural language note using local or hosted AI",
)
async def parse_note_endpoint(request: ParseNoteRequest) -> ParseNoteResponse:
    """
    Parse a natural-language costing note into structured candidate ingredients and expenses.
    
    Safe staging endpoint:
    - Does NOT persist the note or create any database records.
    - Does NOT perform financial calculations or invoke the financial engine.
    - Explicitly surfaces ambiguities and missing fields for user review and confirmation.
    """
    return await parse_costing_note(note=request.note)

