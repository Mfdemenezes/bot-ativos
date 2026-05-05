from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Signal:
    ticker: str
    price: float
    signal: str
    confidence: int
    target1: Optional[float]
    target2: Optional[float]
    stop: Optional[float]
    rr: Optional[float]
    structure: str
    bias: str
    reasons: list = field(default_factory=list)
    forecast: dict = field(default_factory=dict)
    mtf: dict = field(default_factory=dict)
    sentiment: dict = field(default_factory=dict)


def generate(ticker, liq_report, vp, vwap_df, pa_df, forecast, mtf, sentiment, context=None) -> Signal:
    score = 0
    reasons = []
    price = liq_report["price"]
    last_row = pa_df.iloc[-1]

    # 1. Contexto de mercado macro (±25 pts) — novo
    if context:
        macro = context.get("macro_bias", "NEUTRO")
        b, br = context.get("bullish", 0), context.get("bearish", 0)
        total = b + br
        if macro == "ALTA":
            score += 25
            reasons.append(f"✅ Macro ALTA ({b}/{total} correlatos em alta)")
        elif macro == "BAIXA":
            score -= 25
            reasons.append(f"🔴 Macro BAIXA ({br}/{total} correlatos em baixa)")
        elif macro == "MISTO":
            reasons.append(f"⚠️ Macro MISTO ({b}↑ {br}↓)")

    # 2. Multi-timeframe (±30 pts)
    mtf_consensus = mtf.get("consensus", "AGUARDAR")
    alignment = mtf.get("alignment", 0)
    if mtf_consensus == "COMPRA":
        score += 20 + alignment * 5
        reasons.append(f"✅ MTF COMPRA ({alignment}/3 TFs)")
    elif mtf_consensus == "VENDA":
        score -= 20 + alignment * 5
        reasons.append(f"🔴 MTF VENDA ({alignment}/3 TFs)")
    else:
        reasons.append("⚠️ MTF sem consenso")

    # 3. Sweep de liquidez (±25 pts)
    sweep = liq_report.get("last_sweep")
    if sweep:
        if sweep["signal"] == "COMPRA":
            score += 25
            reasons.append(f"✅ SSL varado → fechou acima ({sweep['level']:.4f})")
        elif sweep["signal"] == "VENDA":
            score -= 25
            reasons.append(f"🔴 BSL varado → fechou abaixo ({sweep['level']:.4f})")

    # 4. Estrutura (±10 pts)
    structure = liq_report.get("structure", "INDEFINIDO")
    if structure == "ALTA":
        score += 10; reasons.append("✅ Estrutura HH+HL")
    elif structure == "BAIXA":
        score -= 10; reasons.append("🔴 Estrutura LH+LL")

    # 5. FVG (±12 pts)
    for fvg in liq_report.get("fvg_bullish", []):
        if fvg["bottom"] <= price <= fvg["top"]:
            score += 12; reasons.append(f"✅ FVG bullish ({fvg['gap_pct']:.2f}%)"); break
    for fvg in liq_report.get("fvg_bearish", []):
        if fvg["bottom"] <= price <= fvg["top"]:
            score -= 12; reasons.append(f"🔴 FVG bearish ({fvg['gap_pct']:.2f}%)"); break

    # 6. VWAP (±8 pts)
    if "vwap" in vwap_df.columns:
        vwap_val = vwap_df["vwap"].iloc[-1]
        if price < vwap_val:
            score += 8; reasons.append(f"✅ Abaixo VWAP ({vwap_val:.4f})")
        else:
            score -= 4; reasons.append(f"⚠️ Acima VWAP ({vwap_val:.4f})")

    # 7. POC (±8 pts)
    poc = vp.get("poc")
    if poc and abs(price - poc) / poc < 0.005:
        score += 8; reasons.append(f"✅ No POC ({poc:.4f})")

    # 8. RSI (±7 pts)
    rsi_col = [c for c in pa_df.columns if c.startswith("RSI_")]
    if rsi_col:
        rsi = last_row[rsi_col[0]]
        if rsi < 35:   score += 7; reasons.append(f"✅ RSI sobrevendido ({rsi:.1f})")
        elif rsi > 65: score -= 7; reasons.append(f"🔴 RSI sobrecomprado ({rsi:.1f})")

    # 9. Sentimento (±7 pts)
    if sentiment.get("direction") == "bullish":
        score += 7; reasons.append(f"✅ Sentimento bullish ({sentiment.get('articles',0)} notícias)")
    elif sentiment.get("direction") == "bearish":
        score -= 7; reasons.append(f"🔴 Sentimento bearish ({sentiment.get('articles',0)} notícias)")

    # 10. Chronos (±7 pts)
    if forecast.get("direction") == "ALTA":
        score += 7; reasons.append(f"✅ Chronos alta ({forecast.get('confidence',0):.0%})")
    elif forecast.get("direction") == "BAIXA":
        score -= 7; reasons.append(f"🔴 Chronos baixa ({forecast.get('confidence',0):.0%})")

    if score >= 60:
        sig, t1, t2, stop = "COMPRA", liq_report.get("nearest_bsl"), forecast.get("p90"), liq_report.get("nearest_ssl")
    elif score <= -60:
        sig, t1, t2, stop = "VENDA", liq_report.get("nearest_ssl"), forecast.get("p10"), liq_report.get("nearest_bsl")
    else:
        sig, t1, t2, stop = "AGUARDAR", None, None, None

    rr = round(abs(t1 - price) / abs(price - stop), 2) if t1 and stop and stop != price else None

    return Signal(ticker=ticker, price=price, signal=sig, confidence=min(abs(score), 100),
                  target1=t1, target2=t2, stop=stop, rr=rr, structure=structure,
                  bias=liq_report.get("bias", "NEUTRO"), reasons=reasons,
                  forecast=forecast, mtf=mtf, sentiment=sentiment)
