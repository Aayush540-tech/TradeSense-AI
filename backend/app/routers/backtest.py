import logging
from typing import List
from fastapi import APIRouter
from app.services.backtest_service import backtest_engine
from app.schemas.backtest import BacktestRequest, BacktestResult, SampleStrategy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backtest", tags=["Conversational No-Code Backtesting"])


@router.post("/run", response_model=BacktestResult)
async def run_conversational_backtest(request: BacktestRequest):
    """
    Translates a natural language strategy prompt (e.g. 'Buy Nifty when 5-min crosses 200 EMA')
    into quantitative rules, simulates execution on historical 5-minute candlestick data,
    and returns Win Rate, Max Drawdown, Sharpe Ratio, and Equity Curve data for charting.
    """
    return backtest_engine.run_backtest(request)


@router.get("/strategies/sample", response_model=List[SampleStrategy])
async def get_sample_backtest_strategies():
    """
    Returns popular pre-configured Indian market strategies for one-click testing in the frontend.
    """
    return backtest_engine.get_sample_strategies()
