import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_root_serves_html_dashboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        content = res.text
        assert "TradeSense AI" in content
        assert "Emotional Discipline Score" in content
        assert "Gemini 1.5 Flash Copilot" in content
        assert "Conversational Strategy Backtesting" in content
        assert "SEBI" in content
        assert "Retail F&O Reality" in content
        assert "93%" in content
        assert "Four Intelligent Pillars" in content
        assert "Autonomous Risk & Tilt Guardian" in content
        assert "Conversational Backtester" in content
        assert "Vernacular Filing Desk" in content
        assert "Sub-50ms Cloud Run Telemetry" in content
        assert "Capital & Drawdown Shield" in content
        assert "Theta vs Delta Greeks" in content
        assert "Vernacular Multimodal Filing Analyzer" in content
        assert "Statutory Regulatory Notice" in content
        assert "tab-btn-active" in content

