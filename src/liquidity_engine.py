import pandas as pd
import numpy as np


class LiquidityEngine:
    def __init__(self, df: pd.DataFrame, swing_length: int = 5, tolerance: float = 0.003):
        self.df = df.copy()
        self.swing_length = swing_length
        self.tolerance = tolerance
        self._find_swings()

    def _find_swings(self):
        n, highs, lows = self.swing_length, [], []
        for i in range(n, len(self.df) - n):
            wh = self.df["High"].iloc[i - n : i + n + 1]
            wl = self.df["Low"].iloc[i - n : i + n + 1]
            if self.df["High"].iloc[i] == wh.max():
                highs.append({"idx": i, "price": self.df["High"].iloc[i], "date": self.df.index[i]})
            if self.df["Low"].iloc[i] == wl.min():
                lows.append({"idx": i, "price": self.df["Low"].iloc[i], "date": self.df.index[i]})
        self.swing_highs = highs
        self.swing_lows = lows

    def buyside_liquidity(self):
        return sorted(self.swing_highs, key=lambda x: x["price"], reverse=True)

    def sellside_liquidity(self):
        return sorted(self.swing_lows, key=lambda x: x["price"])

    def equal_levels(self):
        eq_h, eq_l = [], []
        for lst, out, kind in [(self.swing_highs, eq_h, "EQH"), (self.swing_lows, eq_l, "EQL")]:
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    p1, p2 = lst[i]["price"], lst[j]["price"]
                    if abs(p1 - p2) / p1 <= self.tolerance:
                        out.append({"price": (p1 + p2) / 2, "type": kind, "touches": 2})
        return eq_h, eq_l

    def fair_value_gaps(self, min_gap_pct: float = 0.001):
        fvgs, df = [], self.df
        for i in range(1, len(df) - 1):
            # Bullish FVG
            gap = df["Low"].iloc[i + 1] - df["High"].iloc[i - 1]
            if gap > 0 and gap / df["Close"].iloc[i] >= min_gap_pct:
                fvgs.append({"type": "bullish", "top": df["Low"].iloc[i + 1],
                             "bottom": df["High"].iloc[i - 1], "date": df.index[i],
                             "gap_pct": gap / df["Close"].iloc[i] * 100})
            # Bearish FVG
            gap = df["Low"].iloc[i - 1] - df["High"].iloc[i + 1]
            if gap > 0 and gap / df["Close"].iloc[i] >= min_gap_pct:
                fvgs.append({"type": "bearish", "top": df["Low"].iloc[i - 1],
                             "bottom": df["High"].iloc[i + 1], "date": df.index[i],
                             "gap_pct": gap / df["Close"].iloc[i] * 100})
        current = df["Close"].iloc[-1]
        return [f for f in fvgs if not (
            (f["type"] == "bullish" and current < f["bottom"]) or
            (f["type"] == "bearish" and current > f["top"])
        )]

    def detect_sweeps(self, lookback: int = 3):
        sweeps, df = [], self.df
        bsl = self.buyside_liquidity()
        ssl = self.sellside_liquidity()
        for i in range(lookback, len(df)):
            h, l, c = df["High"].iloc[i], df["Low"].iloc[i], df["Close"].iloc[i]
            for lvl in bsl:
                if lvl["idx"] < i - lookback and h > lvl["price"] and c < lvl["price"]:
                    sweeps.append({"type": "bsl_sweep", "signal": "VENDA",
                                   "level": lvl["price"], "date": df.index[i], "close": c})
            for lvl in ssl:
                if lvl["idx"] < i - lookback and l < lvl["price"] and c > lvl["price"]:
                    sweeps.append({"type": "ssl_sweep", "signal": "COMPRA",
                                   "level": lvl["price"], "date": df.index[i], "close": c})
        return sweeps

    def market_structure(self):
        highs = [(h["idx"], h["price"]) for h in self.swing_highs]
        lows = [(l["idx"], l["price"]) for l in self.swing_lows]
        if len(highs) < 2 or len(lows) < 2:
            return "INDEFINIDO"
        hh = highs[-1][1] > highs[-2][1]
        hl = lows[-1][1] > lows[-2][1]
        lh = highs[-1][1] < highs[-2][1]
        ll = lows[-1][1] < lows[-2][1]
        if hh and hl:
            return "ALTA"
        if lh and ll:
            return "BAIXA"
        return "LATERAL"

    def report(self):
        eq_h, eq_l = self.equal_levels()
        fvgs = self.fair_value_gaps()
        sweeps = self.detect_sweeps()
        bsl = self.buyside_liquidity()[:3]
        ssl = self.sellside_liquidity()[:3]
        last_sweep = sweeps[-1] if sweeps else None
        structure = self.market_structure()
        current = self.df["Close"].iloc[-1]

        bias = "NEUTRO"
        if last_sweep:
            bias = last_sweep["signal"]

        return {
            "price": current,
            "structure": structure,
            "bias": bias,
            "nearest_bsl": bsl[0]["price"] if bsl else None,
            "nearest_ssl": ssl[0]["price"] if ssl else None,
            "equal_highs": eq_h,
            "equal_lows": eq_l,
            "fvg_bullish": [f for f in fvgs if f["type"] == "bullish"],
            "fvg_bearish": [f for f in fvgs if f["type"] == "bearish"],
            "last_sweep": last_sweep,
        }
