from .data_fetcher import fetch
from .liquidity_engine import LiquidityEngine
from .volume_profile import vwap_bands
from .price_action import indicators


def _bias(df) -> str:
    liq = LiquidityEngine(df)
    structure = liq.market_structure()
    sweeps = liq.detect_sweeps()
    last_sweep = sweeps[-1]["signal"] if sweeps else None

    df_ind = indicators(df)
    rsi_col = [c for c in df_ind.columns if c.startswith("RSI_")]
    rsi = df_ind[rsi_col[0]].iloc[-1] if rsi_col else 50

    df_vwap = vwap_bands(df)
    price = df["Close"].iloc[-1]
    above_vwap = price > df_vwap["vwap"].iloc[-1]

    score = 0
    if structure == "ALTA": score += 2
    elif structure == "BAIXA": score -= 2
    if last_sweep == "COMPRA": score += 3
    elif last_sweep == "VENDA": score -= 3
    if rsi < 40: score += 1
    elif rsi > 60: score -= 1
    if not above_vwap: score += 1
    else: score -= 1

    if score >= 3: return "COMPRA"
    if score <= -3: return "VENDA"
    return "NEUTRO"


def analyze(ticker: str) -> dict:
    """
    Retorna alinhamento de bias em 3 timeframes.
    Sinal só é válido se pelo menos 2 de 3 concordam.
    """
    configs = [
        ("1d",  "6mo",  "diário"),
        ("4h",  "60d",  "4h"),
        ("1h",  "30d",  "1h"),
    ]
    results = {}
    for interval, period, label in configs:
        try:
            df = fetch(ticker, period=period, interval=interval)
            results[label] = _bias(df)
        except Exception:
            results[label] = "NEUTRO"

    votes = list(results.values())
    buy_votes  = votes.count("COMPRA")
    sell_votes = votes.count("VENDA")

    if buy_votes >= 2:
        consensus = "COMPRA"
    elif sell_votes >= 2:
        consensus = "VENDA"
    else:
        consensus = "AGUARDAR"

    return {
        "timeframes": results,
        "consensus": consensus,
        "alignment": buy_votes if consensus == "COMPRA" else sell_votes if consensus == "VENDA" else 0,
    }
