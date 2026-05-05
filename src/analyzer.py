from .data_fetcher import fetch
from .liquidity_engine import LiquidityEngine
from .volume_profile import compute as vp_compute, vwap_bands, volume_delta
from .price_action import indicators, atr_targets
from .ai_forecast import forecast as ai_forecast
from .multi_timeframe import analyze as mtf_analyze
from .sentiment import fetch_sentiment
from .signal_generator import generate
from .notifier import send_telegram
from . import database as db


def analyze(ticker: str, period: str = "6mo", interval: str = "1d", notify: bool = True) -> dict:
    df = fetch(ticker, period=period, interval=interval)

    # Análises paralelas (independentes)
    liq = LiquidityEngine(df)
    liq_report = liq.report()
    liq_report["structure"] = liq.market_structure()

    vp       = vp_compute(df)
    df_vwap  = vwap_bands(df)
    df_pa    = indicators(df)
    atr      = atr_targets(df_pa)
    fc       = ai_forecast(df)
    mtf      = mtf_analyze(ticker)
    sentiment = fetch_sentiment(ticker)

    sig = generate(ticker, liq_report, vp, df_vwap, df_pa, fc, mtf, sentiment)

    # Fallback targets via ATR
    if not sig.target1 and atr:
        sig.target1 = atr.get("target_long") if sig.signal == "COMPRA" else atr.get("target_short")
    if not sig.stop and atr:
        sig.stop = atr.get("stop_long") if sig.signal == "COMPRA" else atr.get("stop_short")

    db.save_signal(sig)

    if notify and sig.signal != "AGUARDAR":
        send_telegram(sig)

    return {
        "ticker": sig.ticker,
        "price": sig.price,
        "signal": sig.signal,
        "confidence": sig.confidence,
        "target1": sig.target1,
        "target2": sig.target2,
        "stop": sig.stop,
        "rr": sig.rr,
        "structure": sig.structure,
        "bias": sig.bias,
        "reasons": sig.reasons,
        "forecast": sig.forecast,
        "mtf": sig.mtf,
        "sentiment": sig.sentiment,
        "poc": vp["poc"],
        "vah": vp["vah"],
        "val": vp["val"],
    }
