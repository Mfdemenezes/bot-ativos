import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, bins: int = 50) -> dict:
    price_bins = np.linspace(df["Low"].min(), df["High"].max(), bins)
    vol = np.zeros(bins)

    for _, row in df.iterrows():
        mask = (price_bins >= row["Low"]) & (price_bins <= row["High"])
        if mask.sum():
            vol[mask] += row["Volume"] / mask.sum()

    profile = pd.DataFrame({"price": price_bins, "volume": vol})
    poc = profile.loc[profile["volume"].idxmax(), "price"]

    sorted_v = profile.sort_values("volume", ascending=False)
    threshold = sorted_v["volume"].sum() * 0.70
    va = sorted_v[sorted_v["volume"].cumsum() <= threshold]["price"]

    return {"poc": poc, "vah": va.max(), "val": va.min(), "profile": profile}


def vwap_bands(df: pd.DataFrame) -> pd.DataFrame:
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_tp_vol = (tp * df["Volume"]).cumsum()
    cum_vol = df["Volume"].cumsum()
    vwap = cum_tp_vol / cum_vol

    variance = ((tp - vwap) ** 2 * df["Volume"]).cumsum() / cum_vol
    std = np.sqrt(variance)

    df = df.copy()
    df["vwap"] = vwap
    df["vwap_+1"] = vwap + std
    df["vwap_+2"] = vwap + 2 * std
    df["vwap_-1"] = vwap - std
    df["vwap_-2"] = vwap - 2 * std
    return df


def volume_delta(df: pd.DataFrame) -> pd.DataFrame:
    rng = df["High"] - df["Low"] + 1e-9
    buy_vol = df["Volume"] * (df["Close"] - df["Low"]) / rng
    sell_vol = df["Volume"] * (df["High"] - df["Close"]) / rng
    df = df.copy()
    df["delta"] = buy_vol - sell_vol
    df["cum_delta"] = df["delta"].cumsum()
    return df
