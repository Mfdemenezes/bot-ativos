import os
import requests

_EVO_URL      = os.getenv("EVOLUTION_URL", "http://localhost:8082")
_EVO_APIKEY   = os.getenv("EVOLUTION_APIKEY", "evo-api-key-mbam-2026")
_EVO_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "mbam1")
_WA_NUMBER    = os.getenv("WA_NUMBER", "5521960192189")


def send_whatsapp(text: str) -> bool:
    resp = requests.post(
        f"{_EVO_URL}/message/sendText/{_EVO_INSTANCE}",
        json={"number": _WA_NUMBER, "text": text},
        headers={"apikey": _EVO_APIKEY}, timeout=10)
    return resp.ok


def notify(sig, fib=None, vp=None, fc=None, context=None) -> bool:
    text = _format(sig, fib, vp, fc, context)
    ok = send_whatsapp(text)
    if not ok:
        token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    return ok


def _format(sig, fib, vp, fc, context) -> str:
    emoji = {"COMPRA": "🟢 COMPRA", "VENDA": "🔴 VENDA", "AGUARDAR": "🟡 AGUARDAR"}.get(sig.signal, sig.signal)
    rr_str = f"1:{sig.rr}" if sig.rr else "—"

    lines = [
        f"{'─'*28}",
        f"{emoji} *{sig.ticker}*  [{sig.confidence}/100]",
        f"{'─'*28}",
        f"💰 Preço: *{sig.price:.4f}*",
        f"📊 Estrutura: {sig.structure}  |  Bias: {sig.bias}",
    ]

    # Multi-timeframe
    mtf = sig.mtf.get("timeframes", {})
    if mtf:
        lines.append("\n⏱ *Timeframes:*")
        for tf, v in mtf.items():
            e = "✅" if v == "COMPRA" else "🔴" if v == "VENDA" else "➖"
            lines.append(f"  {e} {tf}: {v}")

    # Contexto macro (Nasdaq/correlatos)
    if context and context.get("assets"):
        lines.append("\n🌐 *Contexto Macro:*")
        macro_e = "📈" if context["macro_bias"] == "ALTA" else "📉" if context["macro_bias"] == "BAIXA" else "↔️"
        lines.append(f"  {macro_e} Bias geral: *{context['macro_bias']}*")
        for a in context["assets"]:
            if a.get("bias") == "ERRO": continue
            ae = "✅" if a["bias"] == "ALTA" else "🔴" if a["bias"] == "BAIXA" else "➖"
            lines.append(f"  {ae} {a['ticker']}: {a['price']:.2f}  ret5d: {a.get('ret_5d',0):+.1f}%  RSI: {a.get('rsi',0):.0f}")

    # Entrada / Saída
    lines.append("\n🎯 *Entrada / Saída:*")
    if sig.target1: lines.append(f"  T1: {sig.target1:.4f}")
    if sig.target2: lines.append(f"  T2: {sig.target2:.4f}")
    if sig.stop:    lines.append(f"  Stop: {sig.stop:.4f}  (R:R {rr_str})")

    # Fibonacci
    if fib:
        lines.append("\n📐 *Fibonacci:*")
        lines.append(f"  Topo: {fib['high']:.4f}  Fundo: {fib['low']:.4f}")
        ret = fib["retracements"]
        for label, key in [("23%","23%"),("38%","38%"),("50%","50%"),("61%","61%"),("78%","78%")]:
            val = ret.get(key)
            if val:
                marker = " ◀ preço" if abs(val - sig.price) / sig.price < 0.006 else ""
                lines.append(f"  {label}: {val:.4f}{marker}")
        ext = fib["extensions"]
        lines.append(f"  Ext 127%: {list(ext.values())[0]:.4f}")
        lines.append(f"  Ext 161%: {list(ext.values())[2]:.4f}")
        if fib.get("support"):
            lines.append(f"  🟩 Suporte: {fib['support'][0]} → {fib['support'][1]:.4f}")
        if fib.get("resistance"):
            lines.append(f"  🟥 Resistência: {fib['resistance'][0]} → {fib['resistance'][1]:.4f}")

    # Volume Profile
    if vp:
        lines.append("\n📦 *Volume Profile:*")
        lines.append(f"  POC: {vp['poc']:.4f}  VAH: {vp['vah']:.4f}  VAL: {vp['val']:.4f}")

    # Projeção AI
    if fc:
        d_e = "📈" if fc.get("direction") == "ALTA" else "📉"
        lines.append(f"\n🤖 *Projeção ({fc.get('source','')}):*")
        lines.append(f"  {d_e} {fc.get('direction')}  conf: {fc.get('confidence',0):.0%}")
        lines.append(f"  P10: {fc.get('p10',0):.4f}  P50: {fc.get('p50',0):.4f}  P90: {fc.get('p90',0):.4f}")

    # Sentimento
    sent = sig.sentiment
    lines.append(f"\n📰 Sentimento: {sent.get('direction','—')} ({sent.get('articles',0)} notícias)")

    # Razões
    lines.append("\n📋 *Razões:*")
    lines += [f"  {r}" for r in sig.reasons]
    lines.append(f"{'─'*28}")

    return "\n".join(lines)
