from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class TradeOrder(BaseModel):
    order_id: str = Field(..., description="Unique Order Identifier")
    symbol: str = Field(..., description="Traded symbol (e.g. NIFTY24DEC24100CE)")
    transaction_type: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    pnl: Optional[float] = Field(default=0.0, description="Realized PnL from this trade")
    capital_allocated: float = Field(..., gt=0, description="Total margin/capital committed to this trade")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PortfolioState(BaseModel):
    user_id: str = "trader_default"
    total_capital: float = Field(default=500000.0, description="Total trading equity in INR (₹5,00,000)")
    available_margin: float = Field(default=450000.0)
    realized_pnl_today: float = Field(default=0.0)
    unrealized_pnl: float = Field(default=0.0)
    max_daily_drawdown_limit: float = Field(default=25000.0, description="5% max loss circuit limit (₹25,000)")
    total_trades_today: int = Field(default=0)


class BehavioralRiskAlert(BaseModel):
    alert_id: str
    alert_type: Literal["REVENGE_TRADING", "OVER_LEVERAGING", "MAX_DRAWDOWN_BREACH", "COOLDOWN_ACTIVE"]
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    trigger_reason: str
    ai_calm_nudge_en: str
    ai_calm_nudge_hi: str
    cooldown_recommended_minutes: int = 15
    timestamp: str


class DisciplineScorecard(BaseModel):
    user_id: str
    discipline_score: int = Field(..., ge=0, le=100, description="Real-time behavioral score (0-100)")
    risk_level: Literal["SAFE", "MODERATE", "ELEVATED", "DANGEROUS"]
    loss_streak: int = 0
    rapid_trades_30m_count: int = 0
    overleveraged_trades_count: int = 0
    active_cooldown: bool = False
    cooldown_remaining_seconds: int = 0
    actionable_feedback: List[str]
    timestamp: str

