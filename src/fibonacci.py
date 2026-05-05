import pandas as pd


_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]


def compute(df: pd.DataFrame) -> dict:
    """Fibonacci retracement e extensão sobre o último swing significativo."""
    window = df.tail(60)
    high = window["High"].max()
    low  = window["Low"].min()
    rng  = high - low
    current = df["Close"].iloc[-1]

    retracements = {f"{int(l*100)}%": round(high - rng * l, 4) for l in _LEVELS}
    extensions   = {f"ext_{int(l*100)}%": round(low + rng * l, 4) for l in [1.272, 1.414, 1.618, 2.0]}

    # Nível mais próximo do preço atual
    all_levels = {**retracements, **extensions}
    nearest = min(all_levels.items(), key=lambda x: abs(x[1] - current))

    # Suporte e resistência fibo mais próximos
    below = {k: v for k, v in all_levels.items() if v < current}
    above = {k: v for k, v in all_levels.items() if v > current}

    return {
        "high": high,
        "low": low,
        "retracements": retracements,
        "extensions": extensions,
        "nearest_level": nearest,
        "support": max(below.items(), key=lambda x: x[1]) if below else None,
        "resistance": min(above.items(), key=lambda x: x[1]) if above else None,
    }
