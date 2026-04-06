# Money Autopilot (Mostly Hands-Off)

This project gives you a practical starter app that runs monetization loops automatically:

1. **Affiliate SEO page generation** from a product feed.
2. **Sponsorship outreach generation** from an advertiser list.
3. **Revenue event tracking** in SQLite.

> Reality check: no software can legally guarantee profit, but this app automates recurring revenue actions so you can run with minimal intervention.

## Quick start

```bash
python -m app.money_autopilot
```

The command above runs one cycle and outputs JSON with estimated revenue.

## Continuous mode

```bash
python -m app.money_autopilot --interval-minutes 60
```

That runs indefinitely once per hour.

## Files

- `app/money_autopilot.py` – core automation engine.
- `data/products.csv` – affiliate products feed.
- `data/advertisers.json` – sponsor targets.
- `output/` – generated pages, outreach drafts, and SQLite DB.

## Run tests

```bash
pytest -q
```
