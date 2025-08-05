# draftkit (nflverse-first)

A minimal, open-source pipeline that builds a `players.json` for a fantasy draft board
using **nflverse / nfl_data_py** only (no paid feeds). Designed to power a simple Snake/Auction frontend.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e . # for development mode
```

```bash
# Build for 2025 draft prep using blended historical projections (with caching)
python -m draftkit --year 2025 --config config/league-settings.example.yml --cache data_cache

# Advanced: Custom blending parameters
python -m draftkit --year 2025 --config config/league-settings.example.yml \
  --lookback 3 --blend 0.6,0.3,0.1 --per-game --min-games 8 --cache data_cache

# Output
# - public/players.json (points, VORP, tiers, round estimates by position)
# - public/meta.json (build metadata)
```

> **2025 Projections:** Uses blended per-game averages from recent seasons (default: 60% 2024, 30% 2023, 10% 2022) projected to 17 games. This fixes QB VORP issues and provides more stable rankings than single-season data.

> **Network required:** `nfl_data_py` fetches data from the internet on first run; you need network access when building.

## What's included
- **Connectors:** `nflverse.py` loads weekly stats & rosters via nfl_data_py; `dst.py` loads team defense stats; `kicker.py` loads field goal and extra point data.
- **Scoring:** `scoring.py` computes fantasy points from a league config (YAML) for offense, DST, and kickers.
- **VORP & Tiers:** basic replacement-level and tiering (k-means) per position.
- **Bye weeks:** Integration with schedule data for 2025 draft planning.
- **DST Support:** Team defense scoring with sacks, interceptions, points allowed tiers, and special teams TDs.
- **Kicker Support:** Distance-based field goal scoring (0-39, 40-49, 50+ yards) plus extra points.
- **CLI:** `python -m draftkit --year 2025 --config config/league-settings.example.yml`

## Roadmap

**COMPLETED:**
- ✅ Historical lookback + blended per-game projections (fixes QB VORP & stabilizes ranks)
- ✅ Bye week integration for roster planning
- ✅ DST scoring with Yahoo-style point brackets
- ✅ Kicker scoring with distance-based field goals
- ✅ Diagnostics & sanity checks
- ✅ Snake-draft helpers (round estimates, pick-in-round calculations)
- ✅ Parquet cache for instant rebuilds on draft day
- ✅ Meta.json export for build metadata

**TODO:**
- Rookie & role-change overrides for accurate 2025 valuations
- Consistency metrics (weekly floors, standard deviation)
- CSV export for spreadsheet import

---

🚀 Want to contribute? Check the [roadmap](roadmap.md) for detailed implementation plans.
