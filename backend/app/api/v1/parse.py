"""Endpoint for parsing messy natural-language costing notes into structured candidate inputs."""

from fastapi import APIRouter, status

from app.ai.parser import parse_costing_note
from app.ai.schemas import ParseNoteRequest, ParseNoteResponse

router = APIRouter(tags=["ai"])


@router.post(
    "/parse-note",
    response_model=ParseNoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract candidate costing fields from natural language note using local AI",
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

