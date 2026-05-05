import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from src.analyzer import analyze
from src.notifier import send_whatsapp

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

_CACHE = {}  # {ticker: {"signal": "COMPRA", "structure": "ALTA", "last_sweep": {...}}}


def _changed(ticker: str, current: dict) -> tuple[bool, str]:
    """Retorna (mudou?, razão) se houve evento relevante."""
    if ticker not in _CACHE:
        _CACHE[ticker] = current
        return False, ""

    prev = _CACHE[ticker]
    reasons = []

    # 1. Mudança de sinal forte
    if current["signal"] != prev["signal"] and current["confidence"] >= 70:
        reasons.append(f"Sinal mudou: {prev['signal']} → {current['signal']}")

    # 2. Mudança de estrutura
    if current["structure"] != prev["structure"]:
        reasons.append(f"Estrutura: {prev['structure']} → {current['structure']}")

    # 3. Novo sweep de liquidez
    curr_sweep = current.get("last_sweep")
    prev_sweep = prev.get("last_sweep")
    if curr_sweep and curr_sweep != prev_sweep:
        reasons.append(f"Sweep: {curr_sweep['type']} em {curr_sweep['level']:.4f}")

    # 4. Confiança alta (≥80) mesmo sem mudança
    if current["confidence"] >= 80 and prev["confidence"] < 80:
        reasons.append(f"Confiança alta: {current['confidence']}")

    _CACHE[ticker] = current
    return bool(reasons), " | ".join(reasons)


def monitor_loop():
    with open("watchlist.json") as f:
        tickers = sum(json.load(f).values(), [])

    logging.info(f"Monitor iniciado: {tickers}")

    while True:
        now = datetime.now()
        # Só monitora em horário de mercado: 9h-22h seg-sex
        if now.weekday() < 5 and 9 <= now.hour < 22:
            for ticker in tickers:
                try:
                    r = analyze(ticker, notify_=False)
                    changed, reason = _changed(ticker, {
                        "signal": r["signal"],
                        "confidence": r["confidence"],
                        "structure": r["structure"],
                        "last_sweep": r.get("context", {}).get("last_sweep"),
                    })
                    if changed:
                        logging.info(f"🚨 {ticker}: {reason}")
                        msg = f"🚨 *ALERTA {ticker}*\n\n{reason}\n\nSinal: {r['signal']} ({r['confidence']}/100)\nPreço: {r['price']:.4f}"
                        send_whatsapp(msg)
                except Exception as e:
                    logging.error(f"{ticker}: {e}")

        time.sleep(300)  # 5 minutos


if __name__ == "__main__":
    monitor_loop()
