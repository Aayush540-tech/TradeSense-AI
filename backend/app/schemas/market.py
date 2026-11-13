from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class TickData(BaseModel):
    symbol: str
    ltp: float = Field(..., description="Last Traded Price")
    change: float
    change_percent: float
    high: float
    low: float
    open: float
    close: float
    volume: int
    timestamp: str


class OptionChainSummary(BaseModel):
    underlying: str
    spot_price: float
    pcr: float = Field(..., description="Put-Call Ratio (Total Put OI / Total Call OI)")
    atm_strike: float
    atm_iv: float = Field(..., description="At-The-Money Implied Volatility (%)")
    total_ce_oi: int = Field(..., description="Total Call Open Interest")
    total_pe_oi: int = Field(..., description="Total Put Open Interest")
    sentiment: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    timestamp: str


class MarketFeedStatus(BaseModel):
    broker_provider: str
    is_connected: bool
    data_delayed: bool
    cache_latency_ms: float
    ticks_per_second: float
    timestamp: str


class StreamMessage(BaseModel):
    type: Literal["TICK", "OPTION_CHAIN", "RISK_ALERT", "HEARTBEAT"]
    data: Any
    timestamp: str
    latency_ms: float
    is_delayed: bool = False
