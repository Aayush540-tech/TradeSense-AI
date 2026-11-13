import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.risk_engine import risk_engine
from app.schemas.risk import TradeOrder


@pytest.mark.anyio
async def test_normal_trade_no_alert():
    risk_engine.reset_state("test_user_normal")

    order = TradeOrder(
        order_id="ord_safe_1",
        symbol="NIFTY24DEC24150CE",
        transaction_type="BUY",
        quantity=50,
        price=120.0,
        pnl=1500.0,
        capital_allocated=6000.0,  # 1.2% of 500k capital
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    alert = await risk_engine.record_trade(order, user_id="test_user_normal")
    assert alert is None

    scorecard = risk_engine.get_scorecard("test_user_normal")
    assert scorecard.discipline_score == 100
    assert scorecard.risk_level == "SAFE"
    assert not scorecard.active_cooldown


@pytest.mark.anyio
async def test_overleveraging_trigger():
    risk_engine.reset_state("test_user_leverage")

    # Trade allocating 65,000 on 500,000 capital (13% > 10% limit)
    order = TradeOrder(
        order_id="ord_heavy_1",
        symbol="BANKNIFTY24DEC51800CE",
        transaction_type="BUY",
        quantity=150,
        price=433.33,
        pnl=0.0,
        capital_allocated=65000.0,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    alert = await risk_engine.record_trade(order, user_id="test_user_leverage")
    assert alert is not None
    assert alert.alert_type == "OVER_LEVERAGING"
    assert alert.severity == "WARNING"
    assert "10%" in alert.trigger_reason
    assert "अधिकतम 2% जोखिम" in alert.ai_calm_nudge_hi

    scorecard = risk_engine.get_scorecard("test_user_leverage")
    assert scorecard.discipline_score == 85
    assert scorecard.overleveraged_trades_count == 1


@pytest.mark.anyio
async def test_revenge_trading_trigger():
    risk_engine.reset_state("test_user_revenge")
    now = datetime.now(timezone.utc)

    # 1. Initial losing trade
    loss_trade = TradeOrder(
        order_id="ord_loss_1",
        symbol="NIFTY24DEC24100CE",
        transaction_type="BUY",
        quantity=50,
        price=150.0,
        pnl=-3500.0,
        capital_allocated=7500.0,
        timestamp=(now - timedelta(minutes=20)).isoformat()
    )
    await risk_engine.record_trade(loss_trade, user_id="test_user_revenge")

    # 2. Four rapid subsequent trades
    for i in range(2, 6):
        quick_order = TradeOrder(
            order_id=f"ord_quick_{i}",
            symbol="NIFTY24DEC24150PE",
            transaction_type="BUY",
            quantity=50,
            price=110.0,
            pnl=-200.0,
            capital_allocated=5500.0,
            timestamp=(now - timedelta(minutes=18 - (i * 2))).isoformat()
        )
        await risk_engine.record_trade(quick_order, user_id="test_user_revenge")

    # 3. 6th trade within 30 min window (triggering >5 trades in 30 min post-loss)
    trigger_order = TradeOrder(
        order_id="ord_trigger_revenge",
        symbol="BANKNIFTY24DEC51900CE",
        transaction_type="BUY",
        quantity=30,
        price=210.0,
        pnl=-400.0,
        capital_allocated=6300.0,
        timestamp=now.isoformat()
    )
    alert = await risk_engine.record_trade(trigger_order, user_id="test_user_revenge")
    assert alert is not None
    assert alert.alert_type == "REVENGE_TRADING"
    assert alert.severity == "CRITICAL"
    assert alert.cooldown_recommended_minutes == 15
    assert "रिवेंज ट्रेडिंग" in alert.ai_calm_nudge_hi

    scorecard = risk_engine.get_scorecard("test_user_revenge")
    assert scorecard.active_cooldown
    assert scorecard.cooldown_remaining_seconds > 0
    assert scorecard.discipline_score <= 75


@pytest.mark.anyio
async def test_max_drawdown_breach():
    risk_engine.reset_state("test_user_dd")

    # Catastrophic loss exceeding daily limit (₹25,000)
    dd_trade = TradeOrder(
        order_id="ord_dd_breach",
        symbol="NIFTY24DEC24300CE",
        transaction_type="BUY",
        quantity=200,
        price=150.0,
        pnl=-28000.0,
        capital_allocated=30000.0,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    alert = await risk_engine.record_trade(dd_trade, user_id="test_user_dd")
    assert alert is not None
    assert alert.alert_type in ["OVER_LEVERAGING", "MAX_DRAWDOWN_BREACH"]


@pytest.mark.anyio
async def test_simulate_revenge_trading_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/risk/simulate/revenge-trading?user_id=sim_user")
        assert res.status_code == 200
        alert_data = res.json()
        assert alert_data["alert_type"] == "REVENGE_TRADING"
        assert alert_data["severity"] == "CRITICAL"
        assert "ai_calm_nudge_en" in alert_data
        assert "ai_calm_nudge_hi" in alert_data

        # Check scorecard reflects cooldown
        scorecard_res = await ac.get("/api/v1/risk/scorecard?user_id=sim_user")
        assert scorecard_res.status_code == 200
        scorecard = scorecard_res.json()
        assert scorecard["active_cooldown"]
        assert scorecard["discipline_score"] < 100

