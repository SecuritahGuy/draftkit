# draftkid (nflverse-first)

A minimal, open-source pipeline that builds a `players.json` for a fantasy draft board
using **nflverse / nfl_data_py** only (no paid feeds). Designed to power a simple Snake/Auction frontend.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Build for 2025 draft prep using historical data (2024, 2023, 2022)
python -m draftkit --year 2025 --config config/league-settings.example.yml

# Output
# - public/players.json (points, VORP, tiers by position)
```
> **Note:** When using `--year 2025`, the tool automatically pulls historical data from 2024, 2023, and 2022 seasons to help prepare for your 2025 fantasy draft. For other years, it uses data from that specific season.

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
