import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from src import database as db
from src.analyzer import analyze

load_dotenv()
db.init_db()

app = FastAPI(title="Bot Ativos", version="1.0")


@app.get("/analyze/{ticker}")
def analyze_ticker(ticker: str, period: str = "6mo", interval: str = "1d", notify: bool = True):
    try:
        return analyze(ticker.upper(), period=period, interval=interval, notify=notify)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
