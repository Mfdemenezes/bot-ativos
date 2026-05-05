import re
import xml.etree.ElementTree as ET
import requests

_POSITIVE = {"alta", "sobe", "lucro", "recorde", "compra", "crescimento", "supera",
             "buy", "surge", "profit", "record", "growth", "beats", "upgrade", "bullish"}
_NEGATIVE = {"queda", "cai", "prejuízo", "venda", "risco", "corte", "perde",
             "sell", "drop", "loss", "risk", "cut", "downgrade", "bearish", "crash"}


def _score_text(text: str) -> float:
    words = set(re.findall(r'\w+', text.lower()))
    pos = len(words & _POSITIVE)
    neg = len(words & _NEGATIVE)
    total = pos + neg
    return (pos - neg) / total if total else 0.0


def fetch_sentiment(ticker: str) -> dict:
    """Busca notícias gratuitas via RSS e calcula sentimento."""
    clean = ticker.replace(".SA", "")
    feeds = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
        f"https://news.google.com/rss/search?q={clean}+stock&hl=pt-BR&gl=BR&ceid=BR:pt",
    ]
    scores, count = 0.0, 0
    for url in feeds:
        try:
            resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(resp.content)
            for item in root.iter("item"):
                title = item.findtext("title", "")
                desc = item.findtext("description", "")
                scores += _score_text(title + " " + desc)
                count += 1
        except Exception:
            continue

    avg = scores / count if count else 0.0
    return {
        "score": round(avg, 3),       # -1 a +1
        "articles": count,
        "direction": "bullish" if avg > 0.1 else "bearish" if avg < -0.1 else "neutral",
    }
