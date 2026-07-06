"""Orchestration: ingest -> compute -> validate(schema) -> write out/."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from providers import gather  # noqa: E402
from compute import assemble_signals, composite  # noqa: E402


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def load_schema() -> dict:
    return json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def build(cfg: dict) -> dict:
    raw = gather(cfg)
    signals = assemble_signals(raw, cfg["weights"], int(cfg["mom_window"]), int(cfg["ma_window"]))
    usable = [s for s in signals if s["score"] is not None]
    risk_on, label = composite(signals, float(cfg["risk_on_at"]), float(cfg["risk_off_at"]))

    if not usable:
        status, notes = "unavailable", "no market data"
    elif len(usable) < len(signals):
        status, notes = "partial", "some signals missing"
    else:
        status, notes = "active", None

    feed = {
        "service": cfg["service"],
        "schema_version": str(cfg["schema_version"]),
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "ttl_hours": cfg["ttl_hours"],
        "data": {
            "as_of": dt.date.today().isoformat(),
            "risk_on": risk_on,
            "label": label,
            "signals": signals,
            "disclaimer": "Market-conditions barometer, not a prediction and not investment advice.",
        },
    }
    if notes:
        feed["notes"] = notes
    return feed


def main() -> None:
    cfg = load_config()
    feed = build(cfg)
    jsonschema.validate(feed, load_schema())
    out = ROOT / "out"
    (out / "history").mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2)
    (out / "spy_barometer.json").write_text(payload, encoding="utf-8")
    (out / "history" / f"{feed['data']['as_of']}.json").write_text(payload, encoding="utf-8")
    print(f"[spy_barometer] status={feed['status']} risk_on={feed['data']['risk_on']} ({feed['data']['label']})")


if __name__ == "__main__":
    main()
