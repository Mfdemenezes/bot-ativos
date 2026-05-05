import re
import xml.etree.ElementTree as ET
import requests

_POSITIVE = {
    "alta", "sobe", "subiu", "lucro", "recorde", "compra", "crescimento", "supera",
    "valoriza", "ganho", "positivo", "recupera", "forte",
    "buy", "surge", "surges", "profit", "record", "growth", "beats", "upgrade",
    "bullish", "rally", "rises", "gains", "strong", "outperform", "higher", "up",
}
_NEGATIVE = {
    "queda", "cai", "caiu", "prejuízo", "venda", "risco", "corte", "perde",
    "desvaloriza", "fraco", "negativo", "colapso",
    "sell", "drop", "drops", "loss", "risk", "cut", "downgrade", "bearish",
    "crash", "fear", "falls", "lower", "down", "weak", "underperform", "decline",
}


def _translate(text: str) -> str:
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target="pt").translate(text)
    except Exception:
        return text


def _score_text(text: str) -> float:
    words = set(re.findall(r'\w+', text.lower()))
    pos = len(words & _POSITIVE)
    neg = len(words & _NEGATIVE)
    total = pos + neg
    return (pos - neg) / total if total else 0.0


def fetch_sentiment(ticker: str) -> dict:
    clean = ticker.replace(".SA", "").replace("=X", "")
    feeds = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
        f"https://news.google.com/rss/search?q={clean}+stock&hl=pt-BR&gl=BR&ceid=BR:pt",
    ]
    scores, headlines = [], []
    for url in feeds:
        try:
            resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(resp.content)
            for item in root.iter("item"):
                title = item.findtext("title", "").strip()
                desc  = item.findtext("description", "")
                s = _score_text(title + " " + desc)
                scores.append(s)
                if title and abs(s) >= 0.05:
                    headlines.append((abs(s), title))
        except Exception:
            continue

    avg = sum(scores) / len(scores) if scores else 0.0
    direction = "bullish" if avg > 0.05 else "bearish" if avg < -0.05 else "neutral"

    # Traduz as 3 manchetes mais relevantes
    top_raw = [t for _, t in sorted(headlines, reverse=True)[:3]]
    top = [_translate(t) for t in top_raw]

    return {
        "score": round(avg, 3),
        "articles": len(scores),
        "direction": direction,
        "headlines": top if direction != "neutral" else [],
    }
