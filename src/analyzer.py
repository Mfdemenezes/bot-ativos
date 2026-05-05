from .data_fetcher import fetch
from .liquidity_engine import LiquidityEngine
from .volume_profile import compute as vp_compute, vwap_bands
from .price_action import indicators, atr_targets
from .ai_forecast import forecast as ai_forecast
from .multi_timeframe import analyze as mtf_analyze
from .sentiment import fetch_sentiment
from .fibonacci import compute as fib_compute
from .signal_generator import generate
from .notifier import notify
from . import database as db

db.init_db()


def analyze(ticker: str, period: str = "6mo", interval: str = "1d", notify_: bool = True) -> dict:
    df = fetch(ticker, period=period, interval=interval)

    liq = LiquidityEngine(df)
    liq_report = liq.report()
    liq_report["structure"] = liq.market_structure()

    vp        = vp_compute(df)
    df_vwap   = vwap_bands(df)
    df_pa     = indicators(df)
    atr       = atr_targets(df_pa)
    fc        = ai_forecast(df)
    mtf       = mtf_analyze(ticker)
    sentiment = fetch_sentiment(ticker)
    fib       = fib_compute(df)

    sig = generate(ticker, liq_report, vp, df_vwap, df_pa, fc, mtf, sentiment)

    if not sig.target1 and atr:
        sig.target1 = atr.get("target_long") if sig.signal == "COMPRA" else atr.get("target_short")
    if not sig.stop and atr:
        sig.stop = atr.get("stop_long") if sig.signal == "COMPRA" else atr.get("stop_short")

    db.save_signal(sig)

    if notify_ and sig.signal != "AGUARDAR":
        notify(sig, fib=fib, vp=vp, fc=fc)

    return {
        "ticker": sig.ticker, "price": sig.price, "signal": sig.signal,
        "confidence": sig.confidence, "target1": sig.target1, "target2": sig.target2,
        "stop": sig.stop, "rr": sig.rr, "structure": sig.structure, "bias": sig.bias,
        "reasons": sig.reasons, "forecast": fc, "mtf": sig.mtf,
        "sentiment": sig.sentiment, "fib": fib,
        "poc": vp["poc"], "vah": vp["vah"], "val": vp["val"],
    }
