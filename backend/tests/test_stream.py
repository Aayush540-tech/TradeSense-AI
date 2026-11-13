import pytest
import asyncio
import json
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient
from app.main import app
from app.core.redis_client import redis_client
from app.services.market_feed import market_feed


@pytest.mark.anyio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "disclaimer" in data


@pytest.mark.anyio
async def test_redis_cache_latency():
    # Verify sub-50ms cache response
    test_key = "test:sub_50ms"
    test_payload = {"index": "NIFTY 50", "ltp": 24150.0}

    await redis_client.set_json(test_key, test_payload, ttl_seconds=10)
    cached = await redis_client.get_json(test_key)
    assert cached == test_payload

    latency = await redis_client.get_latency_ms()
    assert latency < 50.0  # Compliance with Gemini.md sub-50ms requirement


@pytest.mark.anyio
async def test_market_feed_option_chain():
    chain = await market_feed.get_latest_option_chain("NIFTY 50")
    assert chain.underlying == "NIFTY 50"
    assert chain.spot_price > 0
    assert chain.pcr > 0
    assert chain.atm_strike > 0
    assert chain.sentiment in ["BULLISH", "BEARISH", "NEUTRAL"]


@pytest.mark.anyio
async def test_stream_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/stream/status")
        assert response.status_code == 200
        data = response.json()
        assert "broker_provider" in data
        assert "cache_latency_ms" in data


def test_websocket_stream_receives_tick():
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/stream/ws") as websocket:
            raw_data = websocket.receive_text()
            data = json.loads(raw_data)
            assert "type" in data
            assert data["type"] in ["TICK", "OPTION_CHAIN"]
            assert "latency_ms" in data

