from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Signal:
    ticker: str
    price: float
    signal: str          # COMPRA | VENDA | AGUARDAR
    confidence: int      # 0-100
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


def generate(ticker: str, liq_report: dict, vp: dict, vwap_df,
             pa_df, forecast: dict, mtf: dict, sentiment: dict) -> Signal:
    score = 0
    reasons = []
    price = liq_report["price"]
    last_row = pa_df.iloc[-1]

    # 1. Multi-timeframe consensus (±35 pts) — peso mais alto
    mtf_consensus = mtf.get("consensus", "AGUARDAR")
    alignment = mtf.get("alignment", 0)
    if mtf_consensus == "COMPRA":
        pts = 20 + alignment * 5
        score += pts
        reasons.append(f"✅ MTF alinhado COMPRA ({alignment}/3 TFs)")
    elif mtf_consensus == "VENDA":
        pts = 20 + alignment * 5
        score -= pts
        reasons.append(f"🔴 MTF alinhado VENDA ({alignment}/3 TFs)")
    else:
        reasons.append("⚠️ MTF sem consenso — sinal fraco")

    # 2. Sweep de liquidez (±30 pts)
    sweep = liq_report.get("last_sweep")
    if sweep:
        if sweep["signal"] == "COMPRA":
            score += 30
            reasons.append(f"✅ SSL varado → fechou acima ({sweep['level']:.2f})")
        elif sweep["signal"] == "VENDA":
            score -= 30
            reasons.append(f"🔴 BSL varado → fechou abaixo ({sweep['level']:.2f})")

    # 3. Estrutura de mercado (±10 pts)
    structure = liq_report.get("structure", "INDEFINIDO")
    if structure == "ALTA":
        score += 10
        reasons.append("✅ Estrutura HH+HL")
    elif structure == "BAIXA":
        score -= 10
        reasons.append("🔴 Estrutura LH+LL")

    # 4. FVG (±15 pts)
    for fvg in liq_report.get("fvg_bullish", []):
        if fvg["bottom"] <= price <= fvg["top"]:
            score += 15
            reasons.append(f"✅ FVG bullish aberto ({fvg['gap_pct']:.2f}%)")
            break
    for fvg in liq_report.get("fvg_bearish", []):
        if fvg["bottom"] <= price <= fvg["top"]:
            score -= 15
            reasons.append(f"🔴 FVG bearish aberto ({fvg['gap_pct']:.2f}%)")
            break

    # 5. VWAP (±8 pts)
    if "vwap" in vwap_df.columns:
        vwap_val = vwap_df["vwap"].iloc[-1]
        if price < vwap_val:
            score += 8
            reasons.append(f"✅ Abaixo VWAP ({vwap_val:.2f})")
        else:
            score -= 4
            reasons.append(f"⚠️ Acima VWAP ({vwap_val:.2f})")

    # 6. Volume Profile POC (±10 pts)
    poc = vp.get("poc")
    if poc and abs(price - poc) / poc < 0.005:
        score += 10
        reasons.append(f"✅ No POC ({poc:.2f})")

    # 7. RSI (±8 pts)
    rsi_col = [c for c in pa_df.columns if c.startswith("RSI_")]
    if rsi_col:
        rsi = last_row[rsi_col[0]]
        if rsi < 35:
            score += 8
            reasons.append(f"✅ RSI sobrevendido ({rsi:.1f})")
        elif rsi > 65:
            score -= 8
            reasons.append(f"🔴 RSI sobrecomprado ({rsi:.1f})")

    # 8. Sentimento (±9 pts)
    sent_score = sentiment.get("score", 0)
    sent_dir = sentiment.get("direction", "neutral")
    if sent_dir == "bullish":
        score += 9
        reasons.append(f"✅ Sentimento bullish ({sentiment.get('articles', 0)} notícias)")
    elif sent_dir == "bearish":
        score -= 9
        reasons.append(f"🔴 Sentimento bearish ({sentiment.get('articles', 0)} notícias)")

    # 9. Chronos forecast (±8 pts)
    if forecast.get("direction") == "ALTA":
        score += 8
        reasons.append(f"✅ Chronos alta (conf {forecast.get('confidence', 0):.0%})")
    elif forecast.get("direction") == "BAIXA":
        score -= 8
        reasons.append(f"🔴 Chronos baixa (conf {forecast.get('confidence', 0):.0%})")

    # Determina sinal — threshold mais alto = mais seletivo = mais acurado
    if score >= 60:
        sig = "COMPRA"
        target1 = liq_report.get("nearest_bsl")
        target2 = forecast.get("p90")
        stop = liq_report.get("nearest_ssl")
    elif score <= -60:
        sig = "VENDA"
        target1 = liq_report.get("nearest_ssl")
        target2 = forecast.get("p10")
        stop = liq_report.get("nearest_bsl")
    else:
        sig = "AGUARDAR"
        target1 = target2 = stop = None

    rr = None
    if target1 and stop and stop != price:
        rr = round(abs(target1 - price) / abs(price - stop), 2)

    return Signal(
        ticker=ticker, price=price, signal=sig, confidence=min(abs(score), 100),
        target1=target1, target2=target2, stop=stop, rr=rr,
        structure=structure, bias=liq_report.get("bias", "NEUTRO"),
        reasons=reasons, forecast=forecast, mtf=mtf, sentiment=sentiment,
    )
