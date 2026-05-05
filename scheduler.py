import json
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from src.analyzer import analyze

load_dotenv()

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")


def run_watchlist():
    with open("watchlist.json") as f:
        watchlist = json.load(f)
    tickers = watchlist.get("br", []) + watchlist.get("us", [])
    for ticker in tickers:
        try:
            result = analyze(ticker, notify=True)
            print(f"{ticker}: {result['signal']} ({result['confidence']})")
        except Exception as e:
            print(f"{ticker}: erro — {e}")


# B3 fecha às 17h, NYSE às 21h (horário Brasília)
scheduler.add_job(run_watchlist, "cron", day_of_week="mon-fri", hour=17, minute=30)
scheduler.add_job(run_watchlist, "cron", day_of_week="mon-fri", hour=21, minute=30)

if __name__ == "__main__":
    print("Scheduler iniciado...")
    run_watchlist()  # roda imediatamente ao iniciar
    scheduler.start()
