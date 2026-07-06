"""Pure logic — no I/O, unit-testable.

A transparent market-conditions barometer. It is NOT a prediction and NOT advice: it
blends a few well-known risk-on / risk-off signals into a single 0-100 score, and shows
every component so the reader can judge for themselves.
"""
from __future__ import annotations


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score_momentum(ret_mom: float | None) -> float | None:
    if ret_mom is None:
        return None
    return clamp(ret_mom / 5.0)  # +5% over the window -> +1


def score_ma_position(last: float | None, ma: float | None) -> float | None:
    if not last or not ma:
        return None
    return clamp((last - ma) / ma * 100.0 / 5.0)  # +5% above MA -> +1


def score_vix_level(vix: float | None) -> float | None:
    if vix is None:
        return None
    return clamp((20.0 - vix) / 6.0)  # 14 -> +1, 26 -> -1


def score_vix_trend(vix_chg_pct: float | None) -> float | None:
    if vix_chg_pct is None:
        return None
    return clamp(-vix_chg_pct / 15.0)  # VIX +15% -> -1 (risk-off)


def score_gold_trend(gold_ret: float | None) -> float | None:
    if gold_ret is None:
        return None
    return clamp(-gold_ret / 5.0)  # gold up 5% (risk-off asset) -> -1


def score_breadth(pct_above: float | None) -> float | None:
    if pct_above is None:
        return None
    return clamp((pct_above - 50.0) / 30.0)  # 80% above -> +1, 20% -> -1


_SIGNAL_DEFS = [
    ("momentum", "SPY {mom}-day momentum", lambda r: score_momentum(r.get("ret_mom"))),
    ("ma_position", "SPY vs {ma}-day MA", lambda r: score_ma_position(r.get("spy_last"), r.get("spy_ma"))),
    ("vix_level", "VIX level", lambda r: score_vix_level(r.get("vix"))),
    ("vix_trend", "VIX 5-day trend", lambda r: score_vix_trend(r.get("vix_chg_pct"))),
    ("gold_trend", "Gold 20-day trend (inverse)", lambda r: score_gold_trend(r.get("gold_ret"))),
    ("breadth", "Breadth (% above MA)", lambda r: score_breadth(r.get("breadth_pct"))),
]

_RAW_KEYS = {
    "momentum": "ret_mom", "ma_position": "spy_last", "vix_level": "vix",
    "vix_trend": "vix_chg_pct", "gold_trend": "gold_ret", "breadth": "breadth_pct",
}


def assemble_signals(raw: dict, weights: dict, mom_window: int, ma_window: int) -> list[dict]:
    signals = []
    for key, label_tmpl, fn in _SIGNAL_DEFS:
        score = fn(raw)
        signals.append({
            "name": key,
            "label": label_tmpl.format(mom=mom_window, ma=ma_window),
            "value": raw.get(_RAW_KEYS[key]),
            "score": None if score is None else round(score, 2),
            "weight": float(weights.get(key, 1.0)),
        })
    return signals


def composite(signals: list[dict], risk_on_at: float, risk_off_at: float) -> tuple[int, str]:
    usable = [s for s in signals if s["score"] is not None]
    tw = sum(s["weight"] for s in usable)
    if tw == 0:
        return 50, "neutral"
    raw = sum(s["score"] * s["weight"] for s in usable) / tw  # -1..1
    risk_on = round((raw + 1.0) / 2.0 * 100.0)
    label = "risk-on" if risk_on >= risk_on_at else ("risk-off" if risk_on <= risk_off_at else "neutral")
    return risk_on, label
