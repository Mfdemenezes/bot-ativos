import os
from datetime import datetime
from sqlalchemy import create_engine, text

_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///bot_ativos.db"))
    return _engine


def init_db():
    with engine().connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL,
                price REAL,
                signal TEXT,
                confidence INTEGER,
                target1 REAL,
                target2 REAL,
                stop REAL,
                rr REAL,
                structure TEXT,
                bias TEXT,
                reasons TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


def save_signal(sig):
    with engine().connect() as conn:
        conn.execute(text("""
            INSERT INTO signals (ticker, price, signal, confidence, target1, target2, stop, rr, structure, bias, reasons)
            VALUES (:ticker, :price, :signal, :confidence, :target1, :target2, :stop, :rr, :structure, :bias, :reasons)
        """), {
            "ticker": sig.ticker, "price": sig.price, "signal": sig.signal,
            "confidence": sig.confidence, "target1": sig.target1, "target2": sig.target2,
            "stop": sig.stop, "rr": sig.rr, "structure": sig.structure,
            "bias": sig.bias, "reasons": "\n".join(sig.reasons),
        })
        conn.commit()
