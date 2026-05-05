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


def generate(ticker: str, liq_report: dict, vp: dict, vwap_df, pa_df, forecast: dict) -> Signal:
    score = 0
    reasons = []
    price = liq_report["price"]
    last_row = pa_df.iloc[-1]

    # 1. Sweep recente (±40 pts)
    sweep = liq_report.get("last_sweep")
    if sweep:
        if sweep["signal"] == "COMPRA":
            score += 40
            reasons.append(f"✅ SSL varado → fechou acima ({sweep['level']:.2f})")
        elif sweep["signal"] == "VENDA":
            score -= 40
            reasons.append(f"🔴 BSL varado → fechou abaixo ({sweep['level']:.2f})")

    # 2. Estrutura de mercado (±15 pts)
    structure = liq_report.get("structure", "INDEFINIDO")
    if structure == "ALTA":
        score += 15
        reasons.append("✅ Estrutura de alta (HH+HL)")
    elif structure == "BAIXA":
        score -= 15
        reasons.append("🔴 Estrutura de baixa (LH+LL)")

    # 3. FVG (±20 pts)
    for fvg in liq_report.get("fvg_bullish", []):
        if fvg["bottom"] <= price <= fvg["top"]:
            score += 20
            reasons.append(f"✅ Dentro de FVG bullish ({fvg['gap_pct']:.2f}%)")
            break
    for fvg in liq_report.get("fvg_bearish", []):
        if fvg["bottom"] <= price <= fvg["top"]:
            score -= 20
            reasons.append(f"🔴 Dentro de FVG bearish ({fvg['gap_pct']:.2f}%)")
            break

    # 4. VWAP (±10 pts)
    if "vwap" in vwap_df.columns:
        vwap_val = vwap_df["vwap"].iloc[-1]
        if price < vwap_val:
            score += 10
            reasons.append(f"✅ Abaixo do VWAP ({vwap_val:.2f}) — desconto")
        else:
            score -= 5
            reasons.append(f"⚠️ Acima do VWAP ({vwap_val:.2f})")

    # 5. Volume Profile POC (±15 pts)
    poc = vp.get("poc")
    if poc and abs(price - poc) / poc < 0.005:
        score += 15
        reasons.append(f"✅ No POC do Volume Profile ({poc:.2f})")

    # 6. RSI (±10 pts)
    rsi_col = [c for c in pa_df.columns if c.startswith("RSI_")]
    if rsi_col:
        rsi = last_row[rsi_col[0]]
        if rsi < 35:
            score += 10
            reasons.append(f"✅ RSI sobrevendido ({rsi:.1f})")
        elif rsi > 65:
            score -= 10
            reasons.append(f"🔴 RSI sobrecomprado ({rsi:.1f})")

    # 7. Chronos forecast (±10 pts)
    if forecast.get("direction") == "ALTA":
        score += 10
        reasons.append(f"✅ Chronos: alta (conf {forecast.get('confidence', 0):.0%})")
    elif forecast.get("direction") == "BAIXA":
        score -= 10
        reasons.append(f"🔴 Chronos: baixa (conf {forecast.get('confidence', 0):.0%})")

    # Determina sinal
    if score >= 55:
        sig = "COMPRA"
        target1 = liq_report.get("nearest_bsl")
        target2 = forecast.get("p90")
        stop = liq_report.get("nearest_ssl")
    elif score <= -55:
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
        ticker=ticker,
        price=price,
        signal=sig,
        confidence=abs(score),
        target1=target1,
        target2=target2,
        stop=stop,
        rr=rr,
        structure=structure,
        bias=liq_report.get("bias", "NEUTRO"),
        reasons=reasons,
        forecast=forecast,
    )
