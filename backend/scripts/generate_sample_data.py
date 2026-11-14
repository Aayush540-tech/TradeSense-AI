from datetime import datetime, timedelta, time
import random
import pandas as pd
import numpy as np


def generate_nifty_candles(days: int = 45) -> pd.DataFrame:
    """
    Generates realistic 5-minute OHLCV candles for NIFTY 50 during Indian market hours (09:15 to 15:30).
    Includes Brownian drift, intraday U-shaped volume, and computes EMA-20, EMA-50, EMA-200, RSI-14.
    """
    records = []
    base_price = 23800.0
    current_close = base_price

    # Market trading hours: 09:15 to 15:30 (75 candles of 5 mins per trading day)
    start_date = datetime.now() - timedelta(days=days * 1.5)
    current_date = start_date

    trading_days_generated = 0
    while trading_days_generated < days:
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        trading_days_generated += 1
        market_open = datetime.combine(current_date.date(), time(9, 15))
        daily_drift = random.gauss(0.0003, 0.004)

        for i in range(75):
            candle_time = market_open + timedelta(minutes=i * 5)
            # Intraday volatility curve
            vol_multiplier = 2.5 if (i < 6 or i > 68) else 1.0
            step = random.gauss(daily_drift * 5, 8.0 * vol_multiplier)

            open_p = round(current_close, 2)
            close_p = round(open_p + step, 2)
            high_p = round(max(open_p, close_p) + abs(random.gauss(0, 4.0)), 2)
            low_p = round(min(open_p, close_p) - abs(random.gauss(0, 4.0)), 2)
            volume = int(random.randint(45000, 180000) * vol_multiplier)

            current_close = close_p
            records.append({
                "timestamp": candle_time.isoformat(),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": volume
            })

        current_date += timedelta(days=1)

    df = pd.DataFrame(records)

    # Calculate Technical Indicators
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean().round(2)
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean().round(2)
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean().round(2)

    # RSI 14
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, np.nan))
    df["rsi_14"] = (100 - (100 / (1 + rs))).fillna(50.0).round(2)

    return df


if __name__ == "__main__":
    df = generate_nifty_candles(days=40)
    out_csv = "data/sample_nifty_5min.csv"
    df.to_csv(out_csv, index=False)
    print(f"Generated {len(df)} 5-min candles saved to {out_csv}")
