import os
import requests


def send_telegram(sig) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    emoji = {"COMPRA": "🟢", "VENDA": "🔴", "AGUARDAR": "🟡"}.get(sig.signal, "⚪")
    rr_str = f"1:{sig.rr}" if sig.rr else "—"

    mtf = sig.mtf.get("timeframes", {})
    mtf_str = " | ".join(f"{k}: {v}" for k, v in mtf.items())

    sent = sig.sentiment
    sent_str = f"{sent.get('direction','—')} ({sent.get('articles', 0)} notícias)"

    lines = [
        f"{emoji} *{sig.ticker}* — {sig.signal}  `{sig.confidence}/100`",
        f"Preço: `{sig.price:.2f}`  |  Estrutura: `{sig.structure}`",
        f"MTF: `{mtf_str}`",
        f"Sentimento: `{sent_str}`",
        "",
    ]
    if sig.target1:
        lines.append(f"🎯 T1: `{sig.target1:.2f}`")
    if sig.target2:
        lines.append(f"🎯 T2: `{sig.target2:.2f}`")
    if sig.stop:
        lines.append(f"🛑 Stop: `{sig.stop:.2f}`  R:R `{rr_str}`")

    lines += ["", "📋 *Razões:*"] + [f"  {r}" for r in sig.reasons]

    fc = sig.forecast
    if fc:
        lines += [
            "",
            f"🤖 *{fc.get('source','')}*: P10 `{fc.get('p10',0):.2f}` | P50 `{fc.get('p50',0):.2f}` | P90 `{fc.get('p90',0):.2f}`",
        ]

    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"},
        timeout=10,
    )
    return resp.ok
