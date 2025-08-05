from __future__ import annotations
import json
from pathlib import Path
import typer
from rich import print

from .connectors.nflverse import load_weekly, load_rosters
from .connectors.schedule import load_bye_weeks, get_2025_bye_weeks
from .connectors.dst import load_dst_weekly, load_dst_rosters
from .connectors.kicker import load_kicker_weekly, load_kicker_rosters
from .transforms.scoring import (ScoringConfig, apply_scoring, apply_blended_scoring, 
                                 apply_dst_scoring, apply_dst_blended_scoring,
                                 apply_kicker_scoring, apply_kicker_blended_scoring)
from .transforms.tiers import compute_replacement_and_vorp, add_tiers_kmeans

app = typer.Typer(help="DraftKit builder (nfl_data_py-first)")

def print_diagnostics(players: list[dict], cfg: ScoringConfig):
    """Print per-position replacement baselines and top-12 preview."""
    from rich.table import Table
    from rich.console import Console
    console = Console()
    
    # Group by position
    by_pos = {}
    for p in players:
        pos = p['pos']
        if pos not in by_pos:
            by_pos[pos] = []
        by_pos[pos].append(p)
    
    # Sort each position by points desc
    for pos in by_pos:
        by_pos[pos].sort(key=lambda x: x.get('points', 0), reverse=True)
    
    print("\n[bold cyan]📊 POSITION DIAGNOSTICS[/bold cyan]")
    
    # Per-position summary
    for pos in ['QB', 'RB', 'WR', 'TE']:
        if pos in by_pos:
            pos_players = by_pos[pos]
            count = len(pos_players)
            
            # Find replacement level (this is approximated - the actual calculation is in tiers.py)
            roster_need = cfg.roster.get(pos, 0)
            flex_boost = 1 if pos in cfg.flex_positions else 0
            approx_replacement_idx = (roster_need + flex_boost) * cfg.teams
            
            replacement_points = 0
            if approx_replacement_idx < len(pos_players):
                replacement_points = pos_players[approx_replacement_idx].get('points', 0)
            
            top_points = pos_players[0].get('points', 0) if pos_players else 0
            
            print(f"  [bold]{pos}[/]: {count} players, replacement ~{replacement_points:.1f}pts (#{approx_replacement_idx+1}), top: {top_points:.1f}pts")
    
    # Top-12 overall preview
    all_players = [p for p in players if p.get('vorp', 0) > 0]
    all_players.sort(key=lambda x: x.get('vorp', 0), reverse=True)
    
    table = Table(title="🏆 Top 12 by VORP")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Pos", style="cyan", width=3)
    table.add_column("Points", style="green", justify="right", width=6)
    table.add_column("VORP", style="yellow", justify="right", width=6)
    table.add_column("Tier", style="magenta", justify="center", width=4)
    table.add_column("Bye", style="blue", justify="center", width=3)
    
    for i, player in enumerate(all_players[:12]):
        table.add_row(
            str(i+1),
            player.get('name', 'Unknown'),
            player.get('pos', '?'),
            f"{player.get('points', 0):.1f}",
            f"{player.get('vorp', 0):.1f}",
            str(player.get('tier', '?')),
            str(player.get('bye', '?'))
        )
    
    console.print(table)
    print("")

@app.command()
def build(year: int = typer.Option(..., "--year", "-y"),
          config: Path = typer.Option(..., "--config", "-c"),
          outdir: Path = typer.Option(Path("public"), "--outdir", "-o"),
          lookback: int = typer.Option(3, "--lookback", help="Number of historical years to use for projections"),
          blend: str = typer.Option("0.6,0.3,0.1", "--blend", help="Comma-separated weights for blending years (most recent first)"),
          per_game: bool = typer.Option(True, "--per-game/--total", help="Use per-game projections multiplied by 17 games"),
          min_games: int = typer.Option(8, "--min-games", help="Minimum games played in a season to include in projections")):
    """Build players.json for the given season/year."""
    outdir.mkdir(parents=True, exist_ok=True)

    # Parse blend weights
    blend_weights = [float(w.strip()) for w in blend.split(',')]
    if len(blend_weights) != lookback:
        print(f"[red]Error: blend weights ({len(blend_weights)}) must match lookback ({lookback})[/]")
        return
    
    # Normalize weights to sum to 1.0
    total_weight = sum(blend_weights)
    blend_weights = [w / total_weight for w in blend_weights]

    # Determine which years to pull data from
    if year == 2025:
        # For 2025 draft prep, use recent historical data
        data_years = list(range(2024, 2024 - lookback, -1))  # [2024, 2023, 2022] for lookback=3
        print(f"[bold]Preparing for {year} draft using historical data from {data_years}[/]")
        print(f"[bold]Blend weights: {dict(zip(data_years, blend_weights))}[/]")
    else:
        # For other years, use the requested year (ignore blending parameters)
        data_years = [year]
        print(f"[bold]Loading data for {year} (no blending)[/]")
        per_game = False  # Don't use per-game for historical years

    # 1) Load data
    print(f"[bold]Loading nflverse weekly for {data_years}...[/]")
    weekly = load_weekly(data_years)
    print(f"Weekly rows: {len(weekly)}")

    print(f"[bold]Loading rosters for {data_years}...[/]")
    rosters = load_rosters(data_years)

    # Load DST data
    print(f"[bold]Loading DST weekly for {data_years}...[/]")
    dst_weekly = load_dst_weekly(data_years)
    print(f"DST weekly rows: {len(dst_weekly)}")

    print(f"[bold]Loading DST rosters for {data_years}...[/]")
    dst_rosters = load_dst_rosters(data_years)
    print(f"DST roster rows: {len(dst_rosters)}")

    # Load kicker data
    print(f"[bold]Loading kicker weekly for {data_years}...[/]")
    kicker_weekly = load_kicker_weekly(data_years)
    print(f"Kicker weekly rows: {len(kicker_weekly)}")

    print(f"[bold]Loading kicker rosters for {year}...[/]")
    kicker_rosters = load_kicker_rosters(year)
    print(f"Kicker roster rows: {len(kicker_rosters)}")

    # Load bye weeks
    print(f"[bold]Loading bye weeks for {year}...[/]")
    if year == 2025:
        bye_weeks = get_2025_bye_weeks()
    else:
        bye_weeks = load_bye_weeks(year)
    print(f"Bye weeks loaded for {len(bye_weeks)} teams")

    # 2) Load scoring config
    cfg = ScoringConfig.from_yaml(config)

    # 3) Score players (offense + DST)
    print("[bold]Scoring offensive players...[/]")
    if year == 2025 and per_game:
        players = apply_blended_scoring(weekly, rosters, cfg, data_years, blend_weights, min_games, bye_weeks)
    else:
        players = apply_scoring(weekly, rosters, cfg, bye_weeks)

    print("[bold]Scoring DST units...[/]")
    if year == 2025 and per_game:
        dst_players = apply_dst_blended_scoring(dst_weekly, dst_rosters, cfg, data_years, blend_weights, min_games, bye_weeks)
    else:
        dst_players = apply_dst_scoring(dst_weekly, dst_rosters, cfg, bye_weeks)

    print("[bold]Scoring kickers...[/]")
    if year == 2025 and per_game:
        kicker_players = apply_kicker_blended_scoring(kicker_weekly, kicker_rosters, cfg, data_years, blend_weights, min_games, bye_weeks)
    else:
        kicker_players = apply_kicker_scoring(kicker_weekly, kicker_rosters, cfg, bye_weeks)

    # Combine offensive players, DST, and kickers
    all_players = players + dst_players + kicker_players
    print(f"Total players (offense + DST + K): {len(all_players)}")

    # 4) Replacement + VORP + tiers
    print("[bold]Computing replacement, VORP, tiers...[/]")
    all_players = compute_replacement_and_vorp(all_players, cfg)
    all_players = add_tiers_kmeans(all_players)

    # 5) Print diagnostics
    if year == 2025 and per_game:
        print_diagnostics(all_players, cfg)

    # 6) Export
    outpath = outdir / "players.json"
    with outpath.open("w") as f:
        json.dump(all_players, f, indent=2)
    print(f"[green]Wrote {outpath}[/]")

if __name__ == "__main__":
    app()
