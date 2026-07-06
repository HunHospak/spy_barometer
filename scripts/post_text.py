"""Generate a ready-to-post social snippet from the latest feed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ARROWS = {"risk-on": "▲", "risk-off": "▼", "neutral": "•"}


def main() -> None:
    feed = json.loads((ROOT / "out" / "spy_barometer.json").read_text(encoding="utf-8"))
    d = feed["data"]
    lines = [f"Market barometer — {d['as_of']}"]
    lines.append(f"{ARROWS.get(d['label'], '')} Risk-on score: {d['risk_on']}/100 ({d['label']})")
    ranked = sorted([s for s in d["signals"] if s["score"] is not None],
                    key=lambda s: -abs(s["score"] * s["weight"]))
    for s in ranked[:3]:
        lines.append(f"  {'+' if s['score'] >= 0 else ''}{s['score']:.2f}  {s['label']}")
    lines.append("Conditions, not a forecast · not investment advice · arkenlabs.eu")
    text = "\n".join(lines)
    (ROOT / "out" / "post.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
