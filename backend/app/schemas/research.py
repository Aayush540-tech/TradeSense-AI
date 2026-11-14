from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field


class FilingMetrics(BaseModel):
    revenue_growth_yoy_pct: Optional[float] = Field(default=None, description="YoY revenue growth in %")
    ebitda_margin_delta_bps: Optional[int] = Field(default=None, description="Operating margin change in basis points (+/- bps)")
    pat_growth_yoy_pct: Optional[float] = Field(default=None, description="Profit After Tax change in %")
    debt_impact: Optional[str] = Field(default="Neutral", description="Debt profile impact")


class ResearchRequest(BaseModel):
    document_text: str = Field(..., description="Extracted text from NSE corporate filing or transcript")
    company_name: Optional[str] = Field(default="NSE Listed Entity", description="Target company or symbol")
    announcement_type: Optional[str] = Field(default="Corporate Filing", description="Type of announcement (e.g. Q3 Results, Capex)")
    language: Literal["en", "hi", "gu", "mr"] = Field(default="en", description="Target vernacular language")


class InterviewRequest(BaseModel):
    youtube_url: Optional[str] = Field(default=None, description="YouTube link of CEO/management interview")
    transcript_text: str = Field(..., description="Interview transcript or earnings call transcript text")
    company_name: str = Field(default="NSE Listed Entity", description="Target company or symbol")
    executive_name: Optional[str] = Field(default="Management", description="Spokesperson (e.g. MD & CEO)")
    language: Literal["en", "hi", "gu", "mr"] = Field(default="en", description="Target vernacular language")


class ResearchResponse(BaseModel):
    company_name: str
    announcement_type: str
    executive_summary: str
    financial_metrics: FilingMetrics
    margin_impact: str = Field(..., description="Extracted impact on operating margins/EBITDA")
    management_guidance: List[str]
    key_takeaways: List[str]
    risk_factors: List[str]
    vernacular_summary: str
    language: str
    model: str
    disclaimer: str


class SampleFilingItem(BaseModel):
    id: str
    title: str
    company_name: str
    announcement_type: str
    snippet: str
    language: str
