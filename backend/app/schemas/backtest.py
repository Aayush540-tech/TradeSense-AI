from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Natural language trading strategy description (e.g., 'Buy Nifty when price crosses above 200 EMA')"
    )
    symbol: str = Field(default="NIFTY 50", description="Target index or stock symbol")
    initial_capital: float = Field(default=500000.0, gt=0, description="Starting capital in INR (₹5,00,000)")
    risk_per_trade_pct: float = Field(default=2.0, ge=0.5, le=5.0, description="Risk per trade percentage")
    stop_loss_pct: float = Field(default=0.8, gt=0, description="Stop loss percentage threshold")
    target_pct: float = Field(default=1.6, gt=0, description="Target profit percentage threshold (1:2 R:R)")


class TradeLog(BaseModel):
    trade_id: str
    entry_time: str
    exit_time: str
    type: Literal["BUY", "SELL"]
    entry_price: float
    exit_price: float
    pnl: float
    return_pct: float
    exit_reason: Literal["TARGET_HIT", "STOP_LOSS_HIT", "SESSION_CLOSE"]


class EquityPoint(BaseModel):
    timestamp: str
    equity: float
    drawdown_pct: float


class BacktestResult(BaseModel):
    strategy_name: str
    parsed_rule_summary: str
    symbol: str
    total_candles_analyzed: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    total_return_pct: float
    sharpe_ratio: float
    equity_curve: List[EquityPoint]
    recent_trades: List[TradeLog]
    disclaimer: str


class SampleStrategy(BaseModel):
    id: str
    title: str
    prompt: str
    category: str
    expected_win_rate: str

