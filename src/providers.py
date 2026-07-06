"""Data providers for spy_barometer — all via yfinance (free)."""
from __future__ import annotations

import pandas as pd
import yfinance as yf


def _closes(data, ticker: str, multi: bool) -> pd.Series:
    df = data[ticker] if multi else data
    return df["Close"].dropna()


def _pct(series: pd.Series, window: int) -> float | None:
    if len(series) < window + 1:
        return None
    a, b = float(series.iloc[-1 - window]), float(series.iloc[-1])
    return (b - a) / a * 100.0 if a else None


def gather(cfg: dict) -> dict:
    """Return the raw inputs needed by compute.assemble_signals()."""
    spy = cfg["benchmark"]
    vix = cfg["vix_ticker"]
    gold = cfg["gold_ticker"]
    ma_window = int(cfg["ma_window"])
    mom_window = int(cfg["mom_window"])

    core = yf.download([spy, vix, gold], period="120d", interval="1d",
                       group_by="ticker", auto_adjust=True, threads=True, progress=False)
    raw: dict = {}
    try:
        spy_c = _closes(core, spy, True)
        raw["spy_last"] = float(spy_c.iloc[-1])
        raw["spy_ma"] = float(spy_c.tail(ma_window).mean()) if len(spy_c) >= ma_window else None
        raw["ret_mom"] = _pct(spy_c, mom_window)
    except Exception:
        raw["spy_last"] = raw["spy_ma"] = raw["ret_mom"] = None
    try:
        vix_c = _closes(core, vix, True)
        raw["vix"] = float(vix_c.iloc[-1])
        raw["vix_chg_pct"] = _pct(vix_c, 5)
    except Exception:
        raw["vix"] = raw["vix_chg_pct"] = None
    try:
        gold_c = _closes(core, gold, True)
        raw["gold_ret"] = _pct(gold_c, 20)
    except Exception:
        raw["gold_ret"] = None

    raw["breadth_pct"] = _breadth(cfg.get("breadth_basket", []), ma_window)
    return raw


def _breadth(basket: list[str], ma_window: int) -> float | None:
    if not basket:
        return None
    data = yf.download(basket, period="120d", interval="1d", group_by="ticker",
                       auto_adjust=True, threads=True, progress=False)
    above = 0
    counted = 0
    multi = len(basket) > 1
    for t in basket:
        try:
            c = _closes(data, t, multi)
            if len(c) < ma_window:
                continue
            counted += 1
            if float(c.iloc[-1]) > float(c.tail(ma_window).mean()):
                above += 1
        except Exception:
            continue
    if counted == 0:
        return None
    return round(above / counted * 100.0, 1)
