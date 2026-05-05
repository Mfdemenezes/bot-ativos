import os
import requests

# Evolution API (WhatsApp)
_EVO_URL      = os.getenv("EVOLUTION_URL", "http://localhost:8082")
_EVO_APIKEY   = os.getenv("EVOLUTION_APIKEY", "evo-api-key-mbam-2026")
_EVO_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "mbam1")
_WA_NUMBER    = os.getenv("WA_NUMBER", "5521960192189")


def send_whatsapp(text: str, number: str = None) -> bool:
    url = f"{_EVO_URL}/message/sendText/{_EVO_INSTANCE}"
    resp = requests.post(url, json={"number": number or _WA_NUMBER, "text": text},
                         headers={"apikey": _EVO_APIKEY}, timeout=10)
    return resp.ok


def send_telegram(sig) -> bool:
    """Mantido como fallback caso TELEGRAM_BOT_TOKEN esteja configurado."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    text = _format(sig)
    resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                         json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                         timeout=10)
    return resp.ok


def notify(sig) -> bool:
    text = _format(sig)
    ok = send_whatsapp(text)
    if not ok:
        ok = send_telegram(sig)
    return ok


def _format(sig) -> str:
    emoji = {"COMPRA": "🟢", "VENDA": "🔴", "AGUARDAR": "🟡"}.get(sig.signal, "⚪")
    rr_str = f"1:{sig.rr}" if sig.rr else "—"
    mtf = sig.mtf.get("timeframes", {})
    mtf_str = " | ".join(f"{k}: {v}" for k, v in mtf.items())
    sent = sig.sentiment
    sent_str = f"{sent.get('direction','—')} ({sent.get('articles', 0)} notícias)"

    lines = [
        f"{emoji} *{sig.ticker}* — {sig.signal}  `{sig.confidence}/100`",
        f"Preço: `{sig.price:.2f}`  |  Estrutura: `{sig.structure}`",
        f"MTF: {mtf_str}",
        f"Sentimento: {sent_str}",
        "",
    ]
    if sig.target1: lines.append(f"🎯 T1: `{sig.target1:.2f}`")
    if sig.target2: lines.append(f"🎯 T2: `{sig.target2:.2f}`")
    if sig.stop:    lines.append(f"🛑 Stop: `{sig.stop:.2f}`  R:R `{rr_str}`")
    lines += ["", "📋 Razões:"] + [f"  {r}" for r in sig.reasons]
    fc = sig.forecast
    if fc:
        lines += ["", f"🤖 {fc.get('source','')}: P10 {fc.get('p10',0):.2f} | P50 {fc.get('p50',0):.2f} | P90 {fc.get('p90',0):.2f}"]
    return "\n".join(lines)
