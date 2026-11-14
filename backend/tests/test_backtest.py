import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.backtest_service import backtest_engine
from app.schemas.backtest import BacktestRequest


def test_parse_natural_language_strategies():
    # Test 200 EMA prompt
    rule_ema = backtest_engine.parse_natural_language_strategy("Buy Nifty when 5-min candle crosses above 200 EMA")
    assert rule_ema["slow_ind"] == "ema_200"
    assert rule_ema["condition"] == "crosses_above"

    # Test Golden Cross prompt
    rule_cross = backtest_engine.parse_natural_language_strategy("Test 20 and 50 EMA golden cross strategy")
    assert rule_cross["fast_ind"] == "ema_20"
    assert rule_cross["slow_ind"] == "ema_50"

    # Test RSI oversold prompt
    rule_rsi = backtest_engine.parse_natural_language_strategy("Buy when RSI crosses above 30 from oversold")
    assert rule_rsi["fast_ind"] == "rsi_14"
    assert rule_rsi["slow_ind"] == 30.0


def test_run_backtest_engine():
    req = BacktestRequest(
        prompt="Buy Nifty when price crosses above 200 EMA with 1:2 risk-reward",
        symbol="NIFTY 50",
        initial_capital=500000.0,
        risk_per_trade_pct=2.0,
        stop_loss_pct=0.8,
        target_pct=1.6
    )
    res = backtest_engine.run_backtest(req)
    assert res.total_candles_analyzed >= 1000
    assert res.total_trades > 0
    assert res.win_rate_pct >= 0.0
    assert len(res.equity_curve) > 0
    assert res.profit_factor >= 0.0
    assert "SEBI Compliance Notice" in res.disclaimer


@pytest.mark.anyio
async def test_backtest_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "prompt": "Test buying when 20 EMA crosses above 50 EMA on 5-min chart",
            "symbol": "NIFTY 50",
            "initial_capital": 500000.0,
            "risk_per_trade_pct": 2.0,
            "stop_loss_pct": 1.0,
            "target_pct": 2.0
        }
        res = await ac.post("/api/v1/backtest/run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["strategy_name"] == "EMA 20/50 Momentum Crossover"
        assert data["total_trades"] > 0
        assert "equity_curve" in data
        assert len(data["equity_curve"]) > 0
        assert "disclaimer" in data


@pytest.mark.anyio
async def test_sample_strategies_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/backtest/strategies/sample")
        assert res.status_code == 200
        strategies = res.json()
        assert len(strategies) >= 3
        assert any("200 EMA" in s["title"] for s in strategies)

