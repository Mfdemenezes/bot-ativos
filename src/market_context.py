from .data_fetcher import fetch
from .liquidity_engine import LiquidityEngine
from .price_action import indicators

# Ativos que influenciam cada ticker
_CONTEXT_MAP = {
    "JEPQ": ["QQQ", "AAPL", "NVDA", "MSFT", "META", "AMZN"],
    "JEPI": ["SPY", "JPM", "JNJ", "PG", "KO"],
    "BRL=X": ["DX-Y.NYB", "EWZ", "CL=F"],  # DXY, Brasil ETF, petróleo
}


def _quick_bias(ticker: str) -> dict:
    try:
        df = fetch(ticker, period="1mo", interval="1d")
        liq = LiquidityEngine(df)
        structure = liq.market_structure()
        sweeps = liq.detect_sweeps()
        df_ind = indicators(df)
        rsi_col = [c for c in df_ind.columns if c.startswith("RSI_")]
        rsi = float(df_ind[rsi_col[0]].iloc[-1]) if rsi_col else 50.0

        # Retorno 5d
        ret_5d = (df["Close"].iloc[-1] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100

        bias = "NEUTRO"
        if structure == "ALTA" and ret_5d > 0:
            bias = "ALTA"
        elif structure == "BAIXA" and ret_5d < 0:
            bias = "BAIXA"

        return {
            "ticker": ticker,
            "price": round(float(df["Close"].iloc[-1]), 4),
            "ret_5d": round(ret_5d, 2),
            "structure": structure,
            "rsi": round(rsi, 1),
            "bias": bias,
            "last_sweep": sweeps[-1]["signal"] if sweeps else None,
        }
    except Exception:
        return {"ticker": ticker, "bias": "ERRO"}


def get_context(ticker: str) -> dict:
    """Retorna bias dos ativos correlacionados ao ticker principal."""
    related = _CONTEXT_MAP.get(ticker, [])
    results = [_quick_bias(t) for t in related]

    bullish = sum(1 for r in results if r.get("bias") == "ALTA")
    bearish = sum(1 for r in results if r.get("bias") == "BAIXA")
    total = len([r for r in results if r.get("bias") != "ERRO"])

    if total == 0:
        macro_bias = "NEUTRO"
    elif bullish / total >= 0.6:
        macro_bias = "ALTA"
    elif bearish / total >= 0.6:
        macro_bias = "BAIXA"
    else:
        macro_bias = "MISTO"

    return {
        "macro_bias": macro_bias,
        "bullish": bullish,
        "bearish": bearish,
        "assets": results,
    }
