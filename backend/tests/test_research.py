import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.research_service import research_service
from app.schemas.research import ResearchRequest, InterviewRequest


def test_filing_margin_expansion_analysis():
    sample_text = (
        "Tata Motors announces strong operational performance for Q3. "
        "Consolidated revenue stood at Rs 110,500 crore, up 15% YoY. "
        "EBITDA margins expanded by +90 bps YoY driven by premium vehicle mix and cost reduction. "
        "Free cash flow generation remained positive."
    )
    req = ResearchRequest(
        document_text=sample_text,
        company_name="Tata Motors Ltd",
        announcement_type="Q3 Earnings",
        language="en"
    )
    res = research_service.analyze_filing(req)
    assert res.company_name == "Tata Motors Ltd"
    assert res.financial_metrics.ebitda_margin_delta_bps == 90
    assert "expanded" in res.margin_impact.lower()
    assert len(res.key_takeaways) > 0
    assert len(res.risk_factors) > 0
    assert "SEBI" in res.disclaimer or "TradeSense AI" in res.disclaimer


def test_filing_margin_contraction_analysis():
    sample_text = (
        "Asian Paints Q2 Financial Review: Revenue grew 5% YoY. "
        "EBITDA margins contracted by -120 bps due to crude oil derivative inflation and higher promotional expenditure. "
        "PAT declined 4% YoY."
    )
    req = ResearchRequest(
        document_text=sample_text,
        company_name="Asian Paints Ltd",
        announcement_type="Q2 Results",
        language="en"
    )
    res = research_service.analyze_filing(req)
    assert res.financial_metrics.ebitda_margin_delta_bps == -120
    assert "contracted" in res.margin_impact.lower()


def test_vernacular_outputs():
    text = "Company reports operating margin improvement of +85 bps."

    # Test Hindi
    res_hi = research_service.analyze_filing(ResearchRequest(document_text=text, company_name="Reliance", language="hi"))
    assert "परिचालन मार्जिन" in res_hi.vernacular_summary

    # Test Gujarati
    res_gu = research_service.analyze_filing(ResearchRequest(document_text=text, company_name="Reliance", language="gu"))
    assert "ઓપરેટિંગ માર્જિન" in res_gu.vernacular_summary

    # Test Marathi
    res_mr = research_service.analyze_filing(ResearchRequest(document_text=text, company_name="Reliance", language="mr"))
    assert "ऑपरेटिंग मार्जिन" in res_mr.vernacular_summary


@pytest.mark.anyio
async def test_interview_analysis_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "youtube_url": "https://www.youtube.com/watch?v=sample123",
            "transcript_text": (
                "Interviewer: What is your outlook on margins? "
                "CEO: We expect operating margins to remain steady near 18%, "
                "with potential 50 bps expansion once raw material prices stabilize."
            ),
            "company_name": "Infosys Ltd",
            "executive_name": "Salil Parekh (CEO)",
            "language": "hi"
        }
        res = await ac.post("/api/v1/research/interview", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["company_name"] == "Infosys Ltd"
        assert len(data["management_guidance"]) > 0
        assert "disclaimer" in data


@pytest.mark.anyio
async def test_sample_filings_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/research/samples")
        assert res.status_code == 200
        samples = res.json()
        assert len(samples) >= 3
        assert any(s["company_name"] == "Tata Motors Ltd" for s in samples)

