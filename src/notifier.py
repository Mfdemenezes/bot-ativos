import os
import requests

_EVO_URL      = os.getenv("EVOLUTION_URL", "http://localhost:8082")
_EVO_APIKEY   = os.getenv("EVOLUTION_APIKEY", "evo-api-key-mbam-2026")
_EVO_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "mbam1")
_WA_NUMBER    = os.getenv("WA_NUMBER", "5521960192189")


def send_whatsapp(text: str) -> bool:
    try:
        resp = requests.post(
            f"{_EVO_URL}/message/sendText/{_EVO_INSTANCE}",
            json={"number": _WA_NUMBER, "text": text},
            headers={"apikey": _EVO_APIKEY}, timeout=30)
        return resp.ok
    except Exception:
        return False


def notify(sig, fib=None, vp=None, fc=None, context=None) -> bool:
    text = _format(sig, fib, vp, fc)
    ok = send_whatsapp(text)
    if not ok:
        token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            try:
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                              timeout=15)
            except Exception:
                pass
    return ok


def _format(sig, fib, vp, fc) -> str:
    emoji = {"COMPRA": "🟢 COMPRA", "VENDA": "🔴 VENDA", "AGUARDAR": "🟡 AGUARDAR"}.get(sig.signal, sig.signal)
    rr_str = f"1:{sig.rr}" if sig.rr else "—"
    mtf = sig.mtf.get("timeframes", {})

    lines = [
        f"{'─'*28}",
        f"{emoji} *{sig.ticker}*  [{sig.confidence}/100]",
        f"{'─'*28}",
        f"💰 Preço: *{sig.price:.4f}*",
        f"📊 Estrutura: {sig.structure}  |  Bias: {sig.bias}",
    ]

    if mtf:
        lines.append("\n⏱ *Timeframes:*")
        for tf, v in mtf.items():
            e = "✅" if v == "COMPRA" else "🔴" if v == "VENDA" else "➖"
            lines.append(f"  {e} {tf}: {v}")

    lines.append("\n🎯 *Entrada / Saída:*")
    if sig.target1: lines.append(f"  T1: {sig.target1:.4f}")
    if sig.target2: lines.append(f"  T2: {sig.target2:.4f}")
    if sig.stop:    lines.append(f"  Stop: {sig.stop:.4f}  (R:R {rr_str})")

    if fib:
        lines.append("\n📐 *Fibonacci:*")
        lines.append(f"  Topo: {fib['high']:.4f}  Fundo: {fib['low']:.4f}")
        ret = fib["retracements"]
        for label in ["23%", "38%", "50%", "61%", "78%"]:
            val = ret.get(label)
            if val:
                marker = " ◀ preço" if abs(val - sig.price) / sig.price < 0.006 else ""
                lines.append(f"  {label}: {val:.4f}{marker}")
        ext = list(fib["extensions"].values())
        if len(ext) >= 3:
            lines.append(f"  Ext 127%: {ext[0]:.4f}  Ext 161%: {ext[2]:.4f}")
        if fib.get("support"):
            lines.append(f"  🟩 Suporte: {fib['support'][0]} → {fib['support'][1]:.4f}")
        if fib.get("resistance"):
            lines.append(f"  🟥 Resistência: {fib['resistance'][0]} → {fib['resistance'][1]:.4f}")

    if vp:
        lines.append("\n📦 *Volume Profile:*")
        lines.append(f"  POC: {vp['poc']:.4f}  VAH: {vp['vah']:.4f}  VAL: {vp['val']:.4f}")

    if fc:
        d_e = "📈" if fc.get("direction") == "ALTA" else "📉"
        lines.append(f"\n🤖 *Projeção ({fc.get('source','')}):*")
        lines.append(f"  {d_e} {fc.get('direction')}  conf: {fc.get('confidence',0):.0%}")
        lines.append(f"  P10: {fc.get('p10',0):.4f}  P50: {fc.get('p50',0):.4f}  P90: {fc.get('p90',0):.4f}")

    sent = sig.sentiment
    direction = sent.get("direction", "neutral")
    if direction != "neutral":
        d_e = "📈" if direction == "bullish" else "📉"
        lines.append(f"\n{d_e} *Notícias ({direction}):*")
        for h in sent.get("headlines", []):
            lines.append(f"  • {h}")

    lines.append("\n📋 *Razões:*")
    lines += [f"  {r}" for r in sig.reasons]
    lines.append(f"{'─'*28}")

    return "\n".join(lines)
