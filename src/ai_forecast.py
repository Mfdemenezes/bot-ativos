import numpy as np
import pandas as pd

try:
    import torch
    from chronos import ChronosPipeline
    CHRONOS_AVAILABLE = True
except ImportError:
    CHRONOS_AVAILABLE = False

_pipeline = None  # singleton — carrega uma vez


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        # large = melhor acurácia; small = mais rápido. Troque se RAM for limitada.
        model = "amazon/chronos-t5-large"
        _pipeline = ChronosPipeline.from_pretrained(
            model, device_map="cpu", torch_dtype=torch.float32
        )
    return _pipeline


def forecast(df: pd.DataFrame, periods: int = 10, samples: int = 200) -> dict:
    if not CHRONOS_AVAILABLE:
        return _ema_fallback(df, periods)

    pipeline = _get_pipeline()
    context = torch.tensor(df["Close"].values[-300:], dtype=torch.float32)
    pred = pipeline.predict(context=context, prediction_length=periods, num_samples=samples)
    s = pred[0].numpy()
    current = df["Close"].iloc[-1]

    return {
        "p10": float(np.percentile(s[:, -1], 10)),
        "p50": float(np.percentile(s[:, -1], 50)),
        "p90": float(np.percentile(s[:, -1], 90)),
        "direction": "ALTA" if np.percentile(s[:, -1], 50) > current else "BAIXA",
        "confidence": float(np.mean(s[:, -1] > current)),
        "source": "chronos-large",
    }


def _ema_fallback(df: pd.DataFrame, periods: int) -> dict:
    close = df["Close"].values
    alpha = 2 / (periods + 1)
    ema = close[-1]
    for p in close[-20:]:
        ema = alpha * p + (1 - alpha) * ema
    return {
        "p10": float(ema * 0.97), "p50": float(ema), "p90": float(ema * 1.03),
        "direction": "ALTA" if ema > close[-1] else "BAIXA",
        "confidence": 0.5, "source": "ema_fallback",
    }
