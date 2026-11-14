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

