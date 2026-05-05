import json
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from src.analyzer import analyze

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")


def run_watchlist(label: str):
    logging.info(f"Rodando análise: {label}")
    with open("watchlist.json") as f:
        watchlist = json.load(f)
    tickers = watchlist.get("br", []) + watchlist.get("us", [])
    for ticker in tickers:
        try:
            r = analyze(ticker, notify_=True)
            logging.info(f"  {ticker}: {r['signal']} ({r['confidence']})")
        except Exception as e:
            logging.error(f"  {ticker}: erro — {e}")


# NYSE fecha ~21h (horário Brasília) — análise 21h30
scheduler.add_job(run_watchlist, "cron", day_of_week="mon-fri",
                  hour=21, minute=30, args=["fechamento NYSE"])

# B3 fecha 17h — análise 17h30
scheduler.add_job(run_watchlist, "cron", day_of_week="mon-fri",
                  hour=17, minute=30, args=["fechamento B3"])

# Pré-abertura NYSE — 9h30 NY = 10h30 Brasília
scheduler.add_job(run_watchlist, "cron", day_of_week="mon-fri",
                  hour=10, minute=30, args=["pré-abertura NYSE"])

if __name__ == "__main__":
    logging.info("Scheduler iniciado. Próximas execuções: 10h30 | 17h30 | 21h30 (seg-sex)")
    scheduler.start()
