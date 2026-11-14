import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.research_service import research_service
from app.schemas.research import (
    ResearchRequest,
    InterviewRequest,
    ResearchResponse,
    SampleFilingItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["Vernacular Multimodal Research"])


@router.post("/analyze", response_model=ResearchResponse)
async def analyze_announcement(request: ResearchRequest):
    """
    Parses corporate filings or quarterly announcements using Gemini 1.5 Pro.
    Returns impact on operating margins (in bps), management commentary, and vernacular summaries.
    """
    return research_service.analyze_filing(request)


@router.post("/interview", response_model=ResearchResponse)
async def analyze_interview_transcript(request: InterviewRequest):
    """
    Analyzes CEO / Management interviews (including YouTube transcripts).
    Extracts margin trajectory guidance, forward-looking statements, and vernacular summaries.
    """
    return research_service.analyze_interview(request)


@router.get("/samples", response_model=List[SampleFilingItem])
async def get_sample_filings():
    """
    Provides catalog of pre-loaded Indian corporate filings for quick testing and UI demo.
    """
    return research_service.get_sample_filings()


@router.post("/upload", response_model=ResearchResponse)
async def upload_and_analyze_filing(
    file: UploadFile = File(...),
    company_name: Optional[str] = Form("NSE Listed Company"),
    language: Optional[str] = Form("en")
):
    """
    Direct upload endpoint for NSE corporate filings (PDF or text).
    """
    content_bytes = await file.read()
    try:
        extracted_text = content_bytes.decode("utf-8", errors="ignore")
    except Exception:
        extracted_text = f"Binary content received from {file.filename} ({len(content_bytes)} bytes)."

    req = ResearchRequest(
        document_text=extracted_text,
        company_name=company_name or file.filename,
        announcement_type="Uploaded Filing",
        language=language or "en"
    )
    return research_service.analyze_filing(req)
