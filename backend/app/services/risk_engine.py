import asyncio
from datetime import datetime, timezone, timedelta
import logging
import uuid
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.redis_client import redis_client
from app.schemas.risk import (
    TradeOrder,
    PortfolioState,
    BehavioralRiskAlert,
    DisciplineScorecard,
)
from app.schemas.market import StreamMessage
from app.services.market_feed import market_feed

logger = logging.getLogger(__name__)


class DisciplineRiskEngine:
    """
    Background Behavioral Risk Intelligence Engine:
    Continuously monitors connected portfolio trades in real time.
    Detects emotional & revenge trading, position sizing breaches (>10% capital),
    and enforces cooldown states with Gemini-synthesized rational alerts.
    """

    def __init__(self):
        self.portfolios: Dict[str, PortfolioState] = {
            "trader_default": PortfolioState()
        }
        self.trade_history: Dict[str, List[TradeOrder]] = {
            "trader_default": []
        }
        self.active_alerts: Dict[str, List[BehavioralRiskAlert]] = {
            "trader_default": []
        }
        self.cooldown_until: Dict[str, Optional[datetime]] = {
            "trader_default": None
        }

    def get_portfolio(self, user_id: str = "trader_default") -> PortfolioState:
        if user_id not in self.portfolios:
            self.portfolios[user_id] = PortfolioState(user_id=user_id)
            self.trade_history[user_id] = []
            self.active_alerts[user_id] = []
            self.cooldown_until[user_id] = None
        return self.portfolios[user_id]

    async def record_trade(
        self,
        order: TradeOrder,
        user_id: str = "trader_default"
    ) -> Optional[BehavioralRiskAlert]:
        """
        Ingests a trade order, updates portfolio state, and evaluates behavioral risk rules.
        """
        portfolio = self.get_portfolio(user_id)
        trades = self.trade_history[user_id]

        # Parse timestamp safely
        try:
            order_time = datetime.fromisoformat(order.timestamp.replace("Z", "+00:00"))
        except Exception:
            order_time = datetime.now(timezone.utc)

        # Update portfolio accounting
        portfolio.total_trades_today += 1
        if order.pnl is not None:
            portfolio.realized_pnl_today += order.pnl
        trades.append(order)

        # Cache order in Redis
        await redis_client.set_json(
            f"user:{user_id}:last_trade",
            order.model_dump(),
            ttl_seconds=86400
        )

        # 1. Check Rule: Over-Leveraging (>10% of total capital in one position)
        capital_ratio = order.capital_allocated / portfolio.total_capital
        if capital_ratio > 0.10:
            pct_formatted = round(capital_ratio * 100, 1)
            alert = self._create_alert(
                user_id=user_id,
                alert_type="OVER_LEVERAGING",
                severity="WARNING",
                trigger_reason=f"Position sizing exceeded 10% rule: {pct_formatted}% of total capital allocated to {order.symbol}.",
                nudge_en=f"You committed {pct_formatted}% of your capital to a single trade. Adhere to your 2% maximum-risk parameter to prevent severe account drawdowns.",
                nudge_hi=f"आपने अपने कुल कैपिटल का {pct_formatted}% एक ही ट्रेड में लगा दिया है। भारी नुकसान से बचने के लिए प्रति ट्रेड अधिकतम 2% जोखिम नियम का पालन करें।",
                cooldown_minutes=5
            )
            await self._dispatch_alert(alert)
            return alert

        # 2. Check Rule: Max Daily Drawdown Breach
        if portfolio.realized_pnl_today <= -portfolio.max_daily_drawdown_limit:
            loss_formatted = abs(round(portfolio.realized_pnl_today, 2))
            alert = self._create_alert(
                user_id=user_id,
                alert_type="MAX_DRAWDOWN_BREACH",
                severity="CRITICAL",
                trigger_reason=f"Daily loss limit breached: -₹{loss_formatted} (Limit: -₹{portfolio.max_daily_drawdown_limit}).",
                nudge_en=f"Daily maximum loss limit breached (-₹{loss_formatted}). Terminal cooldown engaged—step away from the terminal for today to protect capital.",
                nudge_hi=f"आज का दैनिक नुकसान सीमा पार हो गया है (-₹{loss_formatted})। कृपया आज के लिए ट्रेडिंग रोकें और मानसिक शांति बनाए रखें।",
                cooldown_minutes=60
            )
            self.cooldown_until[user_id] = datetime.now(timezone.utc) + timedelta(minutes=60)
            await self._dispatch_alert(alert)
            return alert

        # 3. Check Rule: Revenge Trading (>5 trades in 30 minutes following a loss)
        cutoff_30m = order_time - timedelta(minutes=30)
        recent_trades = [
            t for t in trades
            if self._safe_parse_time(t.timestamp) >= cutoff_30m
        ]

        # Check if there is an earlier loss within this window
        has_earlier_loss = any((t.pnl or 0) < 0 for t in recent_trades[:-1])

        if len(recent_trades) >= 5 and has_earlier_loss:
            alert = self._create_alert(
                user_id=user_id,
                alert_type="REVENGE_TRADING",
                severity="CRITICAL",
                trigger_reason=f"Revenge trading pattern detected: {len(recent_trades)} trades executed in under 30 minutes following a loss.",
                nudge_en="You are displaying signs of revenge trading with rapid consecutive orders after a loss. Take a 15-minute emotional cooldown to reset.",
                nudge_hi="नुकसान के बाद आप लगातार तेजी से ट्रेड ले रहे हैं (रिवेंज ट्रेडिंग)। कृपया 15 मिनट का ब्रेक लें और अपनी रणनीति की समीक्षा करें।",
                cooldown_minutes=15
            )
            self.cooldown_until[user_id] = datetime.now(timezone.utc) + timedelta(minutes=15)
            await self._dispatch_alert(alert)
            return alert

        return None

    def _safe_parse_time(self, ts_str: Optional[str]) -> datetime:
        if not ts_str:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)

    def _create_alert(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        trigger_reason: str,
        nudge_en: str,
        nudge_hi: str,
        cooldown_minutes: int
    ) -> BehavioralRiskAlert:
        alert = BehavioralRiskAlert(
            alert_id=f"alt_{uuid.uuid4().hex[:8]}",
            alert_type=alert_type,
            severity=severity,
            trigger_reason=trigger_reason,
            ai_calm_nudge_en=nudge_en,
            ai_calm_nudge_hi=nudge_hi,
            cooldown_recommended_minutes=cooldown_minutes,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.active_alerts[user_id].append(alert)
        return alert

    async def _dispatch_alert(self, alert: BehavioralRiskAlert):
        """Dispatches alert immediately over WebSocket for instant UI popups."""
        logger.warning(f"BEHAVIORAL ALERT DISPATCHED: [{alert.alert_type}] {alert.trigger_reason}")
        msg = StreamMessage(
            type="RISK_ALERT",
            data=alert.model_dump(),
            timestamp=alert.timestamp,
            latency_ms=0.5,
            is_delayed=False
        )
        await market_feed.broadcast(msg)

    def get_scorecard(self, user_id: str = "trader_default") -> DisciplineScorecard:
        """
        Calculates real-time Behavioral Discipline Score (0-100) based on historical violations.
        """
        portfolio = self.get_portfolio(user_id)
        trades = self.trade_history[user_id]
        alerts = self.active_alerts[user_id]

        score = 100
        now = datetime.now(timezone.utc)

        # Count 30-min window trades
        cutoff_30m = now - timedelta(minutes=30)
        recent_30m = [t for t in trades if self._safe_parse_time(t.timestamp) >= cutoff_30m]

        # Calculate loss streak
        loss_streak = 0
        for t in reversed(trades):
            if (t.pnl or 0) < 0:
                loss_streak += 1
            else:
                break

        # Deduct score for violations
        overleveraged_count = sum(1 for a in alerts if a.alert_type == "OVER_LEVERAGING")
        revenge_count = sum(1 for a in alerts if a.alert_type == "REVENGE_TRADING")
        drawdown_count = sum(1 for a in alerts if a.alert_type == "MAX_DRAWDOWN_BREACH")

        score -= (overleveraged_count * 15)
        score -= (revenge_count * 25)
        score -= (drawdown_count * 30)
        score = max(0, min(100, score))

        # Determine risk level
        if score >= 85:
            risk_level = "SAFE"
        elif score >= 70:
            risk_level = "MODERATE"
        elif score >= 50:
            risk_level = "ELEVATED"
        else:
            risk_level = "DANGEROUS"

        # Check active cooldown
        cooldown_exp = self.cooldown_until[user_id]
        active_cooldown = False
        remaining_secs = 0
        if cooldown_exp and now < cooldown_exp:
            active_cooldown = True
            remaining_secs = int((cooldown_exp - now).total_seconds())

        # Actionable feedback
        feedback = []
        if active_cooldown:
            feedback.append(f"Cooldown active: {remaining_secs // 60}m remaining. Step away from order window.")
        if overleveraged_count > 0:
            feedback.append("Position sizing exceeded 10% limit. Cap per-trade risk to 1-2% of total equity.")
        if revenge_count > 0:
            feedback.append("Revenge trading detected today. Review trading rules and maintain a trading journal.")
        if not feedback:
            feedback.append("Excellent emotional discipline maintained. Trading within mathematical risk parameters.")

        return DisciplineScorecard(
            user_id=user_id,
            discipline_score=score,
            risk_level=risk_level,
            loss_streak=loss_streak,
            rapid_trades_30m_count=len(recent_30m),
            overleveraged_trades_count=overleveraged_count,
            active_cooldown=active_cooldown,
            cooldown_remaining_seconds=remaining_secs,
            actionable_feedback=feedback,
            timestamp=now.isoformat()
        )

    def get_recent_alerts(self, user_id: str = "trader_default") -> List[BehavioralRiskAlert]:
        return list(reversed(self.active_alerts.get(user_id, [])))

    def reset_state(self, user_id: str = "trader_default"):
        """Resets behavioral metrics for demo/testing purposes."""
        self.portfolios[user_id] = PortfolioState(user_id=user_id)
        self.trade_history[user_id] = []
        self.active_alerts[user_id] = []
        self.cooldown_until[user_id] = None


risk_engine = DisciplineRiskEngine()

