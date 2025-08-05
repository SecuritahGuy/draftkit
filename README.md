# draftkid (nflverse-first)

A minimal, open-source pipeline that builds a `players.json` for a fantasy draft board
using **nflverse / nfl_data_py** only (no paid feeds). Designed to power a simple Snake/Auction frontend.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Build for 2025 using the included Yahoo-PPR example scoring
python -m draftkit build --year 2025 --config config/league-settings.example.yml

# Output
# - public/players.json (points, VORP, tiers by position)
```
> Note: `nfl_data_py` fetches data from the internet on first run; you need network access when building.

## What’s included
- **Connectors:** `nflverse.py` loads weekly stats & rosters via nfl_data_py.
- **Scoring:** `scoring.py` computes fantasy points from a league config (YAML).
- **VORP & Tiers:** basic replacement-level and tiering (k-means) per position.
- **CLI:** `python -m draftkit build --year 2025 --config config/league-settings.example.yml`

## Roadmap
- Add K/DST scoring modules.
- Optional ADP enrichment (Sleeper/FFC) behind flags.
- Export bye weeks and schedule strength (nflverse schedules).
