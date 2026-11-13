from datetime import datetime, timezone, timedelta
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Query
from app.services.risk_engine import risk_engine
from app.schemas.risk import (
    TradeOrder,
    PortfolioState,
    BehavioralRiskAlert,
    DisciplineScorecard,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/risk", tags=["Discipline & Risk Engine"])


@router.post("/orders/record", response_model=Optional[BehavioralRiskAlert])
async def record_order_and_evaluate_risk(
    order: TradeOrder,
    user_id: str = Query("trader_default", description="User / Trader ID")
):
    """
    Records an executed trade order and runs background behavioral risk rules.
    Returns a BehavioralRiskAlert if revenge trading, over-leveraging, or max drawdown is triggered.
    """
    return await risk_engine.record_trade(order, user_id=user_id)


@router.get("/scorecard", response_model=DisciplineScorecard)
async def get_discipline_scorecard(
    user_id: str = Query("trader_default", description="User / Trader ID")
):
    """
    Calculates and returns the user's live Emotional Discipline Score (0-100),
    loss streak, active cooldown state, and actionable risk feedback.
    """
    return risk_engine.get_scorecard(user_id=user_id)


@router.get("/alerts", response_model=List[BehavioralRiskAlert])
async def get_recent_alerts(
    user_id: str = Query("trader_default", description="User / Trader ID")
):
    """Returns the list of triggered behavioral alerts for the current session."""
    return risk_engine.get_recent_alerts(user_id=user_id)


@router.get("/portfolio", response_model=PortfolioState)
async def get_portfolio_status(
    user_id: str = Query("trader_default", description="User / Trader ID")
):
    """Returns current portfolio balance, available margin, and daily realized PnL."""
    return risk_engine.get_portfolio(user_id=user_id)


@router.post("/simulate/revenge-trading", response_model=BehavioralRiskAlert)
async def simulate_revenge_trading_demo(
    user_id: str = Query("trader_default", description="User ID for simulation")
):
    """
    Demo Trigger for Hackathon Presentations:
    Simulates a losing trade followed by 5 rapid orders in 10 minutes to immediately
    trigger the Gemini Revenge Trading alert and broadcast it over WebSockets.
    """
    now = datetime.now(timezone.utc)

    # Initial losing trade
    trade1 = TradeOrder(
        order_id=f"demo_loss_{uuid.uuid4().hex[:6]}",
        symbol="NIFTY24DEC24200CE",
        transaction_type="BUY",
        quantity=50,
        price=180.0,
        pnl=-4500.0,
        capital_allocated=9000.0,
        timestamp=(now - timedelta(minutes=25)).isoformat()
    )
    await risk_engine.record_trade(trade1, user_id=user_id)

    # 4 intermediate quick trades
    for i in range(2, 6):
        t = TradeOrder(
            order_id=f"demo_quick_{uuid.uuid4().hex[:6]}",
            symbol="NIFTY24DEC24150PE",
            transaction_type="BUY",
            quantity=50,
            price=140.0,
            pnl=-500.0,
            capital_allocated=7000.0,
            timestamp=(now - timedelta(minutes=20 - (i * 2))).isoformat()
        )
        await risk_engine.record_trade(t, user_id=user_id)

    # 6th trade that breaches the >5 trades in 30 minutes rule
    trigger_trade = TradeOrder(
        order_id=f"demo_trigger_{uuid.uuid4().hex[:6]}",
        symbol="BANKNIFTY24DEC51800CE",
        transaction_type="BUY",
        quantity=30,
        price=320.0,
        pnl=-1200.0,
        capital_allocated=9600.0,
        timestamp=now.isoformat()
    )
    alert = await risk_engine.record_trade(trigger_trade, user_id=user_id)
    return alert


@router.post("/simulate/reset")
async def reset_risk_engine(
    user_id: str = Query("trader_default", description="User ID to reset")
):
    """Resets user trade history and scorecard for clean testing."""
    risk_engine.reset_state(user_id=user_id)
    return {"status": "success", "message": f"Risk state reset for user {user_id}"}

