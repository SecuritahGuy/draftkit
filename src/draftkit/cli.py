from __future__ import annotations
import json
from pathlib import Path
import typer
from rich import print

from .connectors.nflverse import load_weekly, load_rosters
from .transforms.scoring import ScoringConfig, apply_scoring
from .transforms.tiers import compute_replacement_and_vorp, add_tiers_kmeans

app = typer.Typer(help="DraftKit builder (nfl_data_py-first)")

@app.command()
def build(year: int = typer.Option(..., "--year", "-y"),
          config: Path = typer.Option(..., "--config", "-c"),
          outdir: Path = typer.Option(Path("public"), "--outdir", "-o")):
    """Build players.json for the given season/year."""
    outdir.mkdir(parents=True, exist_ok=True)

    # Determine which years to pull data from
    if year == 2025:
        # For 2025 draft prep, use recent historical data
        data_years = [2024, 2023, 2022]
        print(f"[bold]Preparing for {year} draft using historical data from {data_years}[/]")
    else:
        # For other years, use the requested year
        data_years = [year]
        print(f"[bold]Loading data for {year}[/]")

    # 1) Load data
    print(f"[bold]Loading nflverse weekly for {data_years}...[/]")
    weekly = load_weekly(data_years)
    print(f"Weekly rows: {len(weekly)}")

    print(f"[bold]Loading rosters for {data_years}...[/]")
    rosters = load_rosters(data_years)

    # 2) Load scoring config
    cfg = ScoringConfig.from_yaml(config)

    # 3) Score players (offense only, v0)
    print("[bold]Scoring players...[/]")
    players = apply_scoring(weekly, rosters, cfg)

    # 4) Replacement + VORP + tiers
    print("[bold]Computing replacement, VORP, tiers...[/]")
    players = compute_replacement_and_vorp(players, cfg)
    players = add_tiers_kmeans(players)

    # 5) Export
    outpath = outdir / "players.json"
    with outpath.open("w") as f:
        json.dump(players, f, indent=2)
    print(f"[green]Wrote {outpath}[/]")

if __name__ == "__main__":
    app()
