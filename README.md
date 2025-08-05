# draftkid (nflverse-first)

A minimal, open-source pipeline that builds a `players.json` for a fantasy draft board
using **nflverse / nfl_data_py** only (no paid feeds). Designed to power a simple Snake/Auction frontend.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Build for 2025 draft prep using blended historical projections
python -m draftkit --year 2025 --config config/league-settings.example.yml

# Advanced: Custom blending parameters
python -m draftkit --year 2025 --config config/league-settings.example.yml \
  --lookback 3 --blend 0.6,0.3,0.1 --per-game --min-games 8

# Output
# - public/players.json (points, VORP, tiers by position)
```
> **2025 Projections:** Uses blended per-game averages from recent seasons (default: 60% 2024, 30% 2023, 10% 2022) projected to 17 games. This fixes QB VORP issues and provides more stable rankings than single-season data.

> **Network required:** `nfl_data_py` fetches data from the internet on first run; you need network access when building.

## What’s included
- **Connectors:** `nflverse.py` loads weekly stats & rosters via nfl_data_py.
- **Scoring:** `scoring.py` computes fantasy points from a league config (YAML).
- **VORP & Tiers:** basic replacement-level and tiering (k-means) per position.
- **CLI:** `python -m draftkit --year 2025 --config config/league-settings.example.yml`

## Roadmap
- Add K/DST scoring modules.
- Optional ADP enrichment (Sleeper/FFC) behind flags.
- Export bye weeks and schedule strength (nflverse schedules).
