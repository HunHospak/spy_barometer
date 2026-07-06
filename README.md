# spy_barometer

Independent ArkenLabs satellite service. A transparent **market-conditions barometer**: it blends a
handful of risk-on / risk-off signals into a single 0-100 `risk_on` score with a `risk-on / neutral /
risk-off` label, and publishes every component so readers judge for themselves.

**Honest scope:** this is NOT a prediction and NOT investment advice. It describes today's conditions,
not tomorrow's direction. The feed and the Arken panel both say so.

## Signals (all via yfinance, free)
- SPY momentum (20d) and SPY vs its 50-day MA
- VIX level and VIX 5-day trend
- Gold 20-day trend (inverse — gold is a risk-off asset)
- Breadth: % of a large-cap basket trading above their MA

Each maps to a score in [-1, +1] (risk-on positive), weighted, then rescaled to 0-100. All weights,
windows, and the basket live in `config.yaml`.

## Run locally
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python src/build_feed.py       # writes out/spy_barometer.json + history
python scripts/post_text.py    # writes out/post.txt
```

## Deploy
`.github/workflows/publish.yml` runs weekday cron, builds, publishes `out/` to GitHub Pages:
`https://<user>.github.io/spy_barometer/spy_barometer.json`. No secrets required.

## Independence
Knows nothing about Arken. Arken knows only the feed URL + the shared schema. Either can change or die
without breaking the other.
