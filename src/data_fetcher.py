import yfinance as yf
import pandas as pd


def fetch(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"Sem dados para {ticker}")
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def fetch_info(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info
    return {
        "name": info.get("longName", ticker),
        "currency": info.get("currency", ""),
        "market_cap": info.get("marketCap"),
        "sector": info.get("sector", ""),
    }
