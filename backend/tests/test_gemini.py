import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.guardrails import validate_user_intent, ensure_disclaimer, MANDATORY_SYSTEM_PROMPT


@pytest.mark.anyio
async def test_guardrail_blocks_direct_buy_sell():
    # Direct advice query must be intercepted and rejected
    forbidden_queries = [
        "Should I buy Nifty 24200 Call option today?",
        "Which stock to buy today for quick profit?",
        "Give me a target price for BankNifty",
        "Will Nifty crash tomorrow?",
        "Kon sa stock kharide aaj?",
    ]
    for q in forbidden_queries:
        is_compliant, refusal = validate_user_intent(q)
        assert not is_compliant, f"Failed to block prohibited query: {q}"
        assert "SEBI Compliance Notice" in refusal
        assert "TradeSense AI is strictly an educational" in refusal


@pytest.mark.anyio
async def test_guardrail_allows_analytical_queries():
    compliant_queries = [
        "What is the mathematical definition of Put-Call Ratio (PCR)?",
        "How does an implied volatility of 18% impact option straddle pricing?",
        "Explain max drawdown rule in risk management.",
        "What is the current NIFTY 50 PCR indicating?",
    ]
    for q in compliant_queries:
        is_compliant, refusal = validate_user_intent(q)
        assert is_compliant, f"Erroneously blocked compliant query: {q}"
        assert refusal is None


@pytest.mark.anyio
async def test_chat_query_endpoint_analytical():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "message": "What does a PCR of 1.25 indicate for market risk?",
            "language": "en",
            "include_market_context": True,
        }
        res = await ac.post("/api/v1/chat/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert not data["is_refused"]
        assert "Put-Call Ratio" in data["reply"]
        assert "disclaimer" in data
        assert data["latency_ms"] >= 0


@pytest.mark.anyio
async def test_chat_refusal_via_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "message": "Which stock to buy today?",
            "language": "en",
        }
        res = await ac.post("/api/v1/chat/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_refused"]
        assert "SEBI Compliance Notice" in data["reply"]


@pytest.mark.anyio
async def test_chat_stream_sse_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "message": "Analyze market drawdown risk",
            "language": "en",
        }
        res = await ac.post("/api/v1/chat/stream", json=payload)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body = res.text
        assert "data:" in body
        assert "[DONE]" in body


@pytest.mark.anyio
async def test_vernacular_chat_hindi():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "message": "Explain risk management rules",
            "language": "hi",
        }
        res = await ac.post("/api/v1/chat/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["language"] == "hi"
        assert "जोखिम" in data["reply"] or "Risk" in data["reply"]


@pytest.mark.anyio
async def test_research_filing_analysis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        sample_filing = (
            "Tata Motors Ltd announces Q3 results. Consolidated revenue grew 15% YoY. "
            "EBITDA margins expanded by +90 bps driven by Jaguar Land Rover operational performance. "
            "Management maintained positive free cash flow guidance."
        )
        payload = {
            "document_text": sample_filing,
            "company_name": "Tata Motors Ltd",
            "announcement_type": "Q3 Results",
            "language": "en"
        }
        res = await ac.post("/api/v1/research/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["company_name"] == "Tata Motors Ltd"
        assert "margin_impact" in data
        assert len(data["key_takeaways"]) > 0
        assert len(data["risk_factors"]) > 0
        assert "disclaimer" in data
