import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.gemini_service import gemini_service
from app.schemas.research import ResearchRequest, ResearchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["Vernacular Multimodal Research"])


@router.post("/analyze", response_model=ResearchResponse)
async def analyze_announcement(request: ResearchRequest):
    """
    Parses corporate filings or quarterly announcements using Gemini 1.5 Pro.
    Returns impact on operating margins, management commentary, and vernacular summaries.
    """
    return await gemini_service.analyze_filing(request)


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
    # Decode text or extract raw text representation
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
    return await gemini_service.analyze_filing(req)

