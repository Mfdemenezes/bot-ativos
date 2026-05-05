import os
import requests

_EVO_URL      = os.getenv("EVOLUTION_URL", "http://localhost:8082")
_EVO_APIKEY   = os.getenv("EVOLUTION_APIKEY", "evo-api-key-mbam-2026")
_EVO_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "mbam1")
_WA_NUMBER    = os.getenv("WA_NUMBER", "5521960192189")


def send_whatsapp(text: str, number: str = None) -> bool:
    url = f"{_EVO_URL}/message/sendText/{_EVO_INSTANCE}"
    resp = requests.post(url, json={"number": number or _WA_NUMBER, "text": text},
                         headers={"apikey": _EVO_APIKEY}, timeout=10)
    return resp.ok


def notify(sig, fib: dict = None, vp: dict = None, fc: dict = None) -> bool:
    text = _format(sig, fib, vp, fc)
    ok = send_whatsapp(text)
    if not ok:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                          timeout=10)
    return ok


def _format(sig, fib, vp, fc) -> str:
    emoji = {"COMPRA": "🟢 COMPRA", "VENDA": "🔴 VENDA", "AGUARDAR": "🟡 AGUARDAR"}.get(sig.signal, sig.signal)
    rr_str = f"1:{sig.rr}" if sig.rr else "—"
    mtf = sig.mtf.get("timeframes", {})

    lines = [
        f"{'='*30}",
        f"{emoji} — *{sig.ticker}*",
        f"Confiança: {sig.confidence}/100",
        f"{'='*30}",
        "",
        f"💰 *Preço atual:* {sig.price:.4f}",
        f"📊 *Estrutura:* {sig.structure}  |  Bias: {sig.bias}",
        "",
        "⏱ *Multi-Timeframe:*",
    ]
    for tf, v in mtf.items():
        e = "✅" if v == "COMPRA" else "🔴" if v == "VENDA" else "➖"
        lines.append(f"  {e} {tf}: {v}")

    # Entrada / Saída
    lines += ["", "🎯 *Entrada / Saída:*"]
    if sig.target1: lines.append(f"  T1: {sig.target1:.4f}")
    if sig.target2: lines.append(f"  T2: {sig.target2:.4f}")
    if sig.stop:    lines.append(f"  Stop: {sig.stop:.4f}  (R:R {rr_str})")

    # Projeção Fibonacci
    if fib:
        lines += ["", "📐 *Fibonacci (60 sessões):*",
                  f"  Topo: {fib['high']:.4f}  |  Fundo: {fib['low']:.4f}"]
        ret = fib["retracements"]
        for k in ["23%", "38%", "50%", "61%", "78%"]:
            key = k.replace("%","") + "%"
            # normaliza chave
            val = ret.get(key) or ret.get(k)
            if val:
                marker = " ← preço" if abs(val - sig.price) / sig.price < 0.005 else ""
                lines.append(f"  {k}: {val:.4f}{marker}")
        ext = fib["extensions"]
        lines += [f"  Ext 127%: {ext.get('ext_127%', ext.get('ext_1272%', '—')):.4f}",
                  f"  Ext 161%: {ext.get('ext_161%', ext.get('ext_1618%', '—')):.4f}"]
        if fib.get("support"):
            lines.append(f"  🟩 Suporte fibo: {fib['support'][0]} → {fib['support'][1]:.4f}")
        if fib.get("resistance"):
            lines.append(f"  🟥 Resistência fibo: {fib['resistance'][0]} → {fib['resistance'][1]:.4f}")

    # Liquidez
    lines += ["", "💧 *Zonas de Liquidez:*"]
    if sig.mtf:
        bsl = sig.mtf.get("nearest_bsl") or getattr(sig, "nearest_bsl", None)
        ssl = sig.mtf.get("nearest_ssl") or getattr(sig, "nearest_ssl", None)
    bsl = getattr(sig, "target1", None) if sig.signal == "COMPRA" else None
    ssl = getattr(sig, "stop", None)
    if sig.target1: lines.append(f"  BSL (compra): {sig.target1:.4f}")
    if sig.stop:    lines.append(f"  SSL (venda):  {sig.stop:.4f}")
    sweep = sig.mtf.get("last_sweep") if sig.mtf else None

    # Volume Profile
    if vp:
        lines += ["", "📦 *Volume Profile:*",
                  f"  POC: {vp['poc']:.4f}  (maior volume)",
                  f"  VAH: {vp['vah']:.4f}  (topo da value area)",
                  f"  VAL: {vp['val']:.4f}  (fundo da value area)"]

    # Projeção AI
    if fc:
        direction_emoji = "📈" if fc.get("direction") == "ALTA" else "📉"
        lines += ["", f"🤖 *Projeção {fc.get('source','')}:*",
                  f"  {direction_emoji} Direção: {fc.get('direction')}  (conf {fc.get('confidence',0):.0%})",
                  f"  Pessimista (P10): {fc.get('p10',0):.4f}",
                  f"  Base      (P50): {fc.get('p50',0):.4f}",
                  f"  Otimista  (P90): {fc.get('p90',0):.4f}"]

    # Sentimento
    sent = sig.sentiment
    sent_e = "📰"
    lines += ["", f"{sent_e} *Sentimento:* {sent.get('direction','—')} ({sent.get('articles',0)} notícias)"]

    # Razões
    lines += ["", "📋 *Razões do sinal:*"] + [f"  {r}" for r in sig.reasons]
    lines.append(f"\n{'='*30}")

    return "\n".join(lines)
