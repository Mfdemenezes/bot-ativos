import pandas as pd
import pandas_ta as ta


def indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.ta.rsi(length=14, append=True)
    df.ta.macd(append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.ema(length=21, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    return df


def order_blocks(df: pd.DataFrame, min_move_pct: float = 0.5) -> list:
    obs = []
    for i in range(1, len(df) - 3):
        move = (df["Close"].iloc[i + 3] - df["Close"].iloc[i + 1]) / df["Close"].iloc[i + 1] * 100
        if abs(move) < min_move_pct:
            continue
        direction = "bullish" if move > 0 else "bearish"
        is_ob = (direction == "bullish" and df["Close"].iloc[i] < df["Open"].iloc[i]) or \
                (direction == "bearish" and df["Close"].iloc[i] > df["Open"].iloc[i])
        if is_ob:
            obs.append({
                "type": f"{direction}_ob",
                "high": df["High"].iloc[i],
                "low": df["Low"].iloc[i],
                "date": df.index[i],
                "strength": abs(move),
            })
    return obs


def atr_targets(df: pd.DataFrame, multiplier: float = 2.0) -> dict:
    atr_col = [c for c in df.columns if c.startswith("ATRr_")]
    if not atr_col:
        return {}
    atr = df[atr_col[0]].iloc[-1]
    price = df["Close"].iloc[-1]
    return {
        "atr": atr,
        "target_long": price + multiplier * atr,
        "stop_long": price - multiplier * atr,
        "target_short": price - multiplier * atr,
        "stop_short": price + multiplier * atr,
    }
