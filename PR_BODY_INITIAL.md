Title: feat: initial nfl_data_py pipeline (scoring + VORP + tiers)

This PR introduces the initial nflverse-first pipeline:
- connectors/nflverse.py: weekly+rosters loaders
- transforms/scoring.py: Yahoo-PPR scoring (offense)
- transforms/tiers.py: replacement, VORP, tiering (k-means/quantiles)
- CLI: `python -m draftkit build --year 2025 --config config/league-settings.example.yml`
- CI: GitHub Actions (pytest)

Notes:
- pick-six thrown and sacks taken are defaulted to 0 (not in open weekly datasets)
- K/DST scoring to follow in a separate PR
