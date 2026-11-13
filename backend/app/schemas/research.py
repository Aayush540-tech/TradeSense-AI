from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    document_text: str = Field(..., description="Extracted text from NSE corporate filing or transcript")
    company_name: Optional[str] = Field(default=None, description="Target company / symbol")
    announcement_type: Optional[str] = Field(default="Corporate Announcement", description="Type of filing")
    language: Literal["en", "hi", "gu", "mr"] = Field(default="en", description="Vernacular summary language")


class ResearchResponse(BaseModel):
    company_name: str
    executive_summary: str
    margin_impact: str = Field(..., description="Extracted impact on operating margins/EBITDA")
    key_takeaways: List[str]
    risk_factors: List[str]
    vernacular_summary: str
    language: str
    model: str
    disclaimer: str
