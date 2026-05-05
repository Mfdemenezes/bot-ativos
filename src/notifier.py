import os
import requests


def send_telegram(sig) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    emoji = {"COMPRA": "🟢", "VENDA": "🔴", "AGUARDAR": "🟡"}.get(sig.signal, "⚪")
    rr_str = f"1:{sig.rr}" if sig.rr else "—"

    lines = [
        f"{emoji} *{sig.ticker}* — {sig.signal}",
        f"Preço: `{sig.price:.2f}`  |  Confiança: `{sig.confidence}/100`",
        f"Estrutura: `{sig.structure}`  |  Bias: `{sig.bias}`",
        "",
    ]
    if sig.target1:
        lines.append(f"🎯 Target 1: `{sig.target1:.2f}`")
    if sig.target2:
        lines.append(f"🎯 Target 2: `{sig.target2:.2f}`")
    if sig.stop:
        lines.append(f"🛑 Stop: `{sig.stop:.2f}`  |  R:R `{rr_str}`")
    if sig.reasons:
        lines += ["", "📋 *Razões:*"] + [f"  {r}" for r in sig.reasons]

    forecast = sig.forecast
    if forecast:
        lines += [
            "",
            f"🤖 Forecast ({forecast.get('source','')}):",
            f"  P10: `{forecast.get('p10', 0):.2f}` | P50: `{forecast.get('p50', 0):.2f}` | P90: `{forecast.get('p90', 0):.2f}`",
        ]

    text = "\n".join(lines)
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )
    return resp.ok
