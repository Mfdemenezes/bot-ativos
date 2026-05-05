import numpy as np
import pandas as pd

try:
    import torch
    from chronos import ChronosPipeline
    CHRONOS_AVAILABLE = True
except ImportError:
    CHRONOS_AVAILABLE = False


def forecast(df: pd.DataFrame, periods: int = 10, samples: int = 100) -> dict:
    """
    Retorna previsão probabilística usando Amazon Chronos.
    Fallback para média móvel exponencial se Chronos não disponível.
    """
    if not CHRONOS_AVAILABLE:
        return _ema_fallback(df, periods)

    pipeline = ChronosPipeline.from_pretrained(
        "amazon/chronos-t5-small",
        device_map="cpu",
        torch_dtype=torch.float32,
    )
    context = torch.tensor(df["Close"].values[-200:], dtype=torch.float32)
    pred = pipeline.predict(context=context, prediction_length=periods, num_samples=samples)
    samples_np = pred[0].numpy()

    return {
        "p10": float(np.percentile(samples_np[:, -1], 10)),
        "p50": float(np.percentile(samples_np[:, -1], 50)),
        "p90": float(np.percentile(samples_np[:, -1], 90)),
        "direction": "ALTA" if np.percentile(samples_np[:, -1], 50) > df["Close"].iloc[-1] else "BAIXA",
        "confidence": float(np.mean(samples_np[:, -1] > df["Close"].iloc[-1])),
        "source": "chronos",
    }


def _ema_fallback(df: pd.DataFrame, periods: int) -> dict:
    close = df["Close"].values
    alpha = 2 / (periods + 1)
    ema = close[-1]
    for p in close[-20:]:
        ema = alpha * p + (1 - alpha) * ema
    direction = "ALTA" if ema > close[-1] else "BAIXA"
    return {
        "p10": float(ema * 0.97),
        "p50": float(ema),
        "p90": float(ema * 1.03),
        "direction": direction,
        "confidence": 0.5,
        "source": "ema_fallback",
    }
