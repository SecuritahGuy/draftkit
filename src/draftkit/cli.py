from __future__ import annotations
import json
from pathlib import Path
import typer
from rich import print
import pandas as pd

from .connectors.nflverse import load_weekly, load_rosters
from .connectors.schedule import load_bye_weeks, get_2025_bye_weeks
from .connectors.dst import load_dst_weekly, load_dst_rosters
from .connectors.kicker import load_kicker_weekly, load_kicker_rosters
from .transforms.scoring import (apply_scoring, apply_blended_scoring, ScoringConfig)
from .transforms.scoring_dst import apply_dst_scoring, apply_dst_blended_scoring
from .transforms.scoring_kicker import apply_kicker_scoring, apply_kicker_blended_scoring
from .transforms.tiers import compute_replacement_and_vorp, add_tiers_kmeans

app = typer.Typer(help="DraftKit builder (nfl_data_py-first)")

def load_with_cache(data_years: list[int], cache_dir: Path = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data with optional parquet caching for speed."""
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Load offensive data
    weekly_frames = []
    roster_frames = []
    dst_weekly_frames = []
    dst_roster_frames = []
    kicker_weekly_frames = []
    kicker_roster_frames = []
    
    for year in data_years:
        # Try cache first, fall back to fresh load
        if cache_dir:
            weekly_cache = cache_dir / f"weekly_{year}.parquet"
            roster_cache = cache_dir / f"rosters_{year}.parquet"
            dst_weekly_cache = cache_dir / f"dst_weekly_{year}.parquet"
            dst_roster_cache = cache_dir / f"dst_rosters_{year}.parquet"
            kicker_weekly_cache = cache_dir / f"kicker_weekly_{year}.parquet"
            kicker_roster_cache = cache_dir / f"kicker_rosters_{year}.parquet"
            
            # Load weekly data
            if weekly_cache.exists():
                print(f"[dim]Loading weekly {year} from cache...[/]")
                weekly_year = pd.read_parquet(weekly_cache)
            else:
                print(f"[bold]Loading weekly {year} from nflverse...[/]")
                weekly_year = load_weekly([year])
                weekly_year.to_parquet(weekly_cache)
            
            # Load roster data
            if roster_cache.exists():
                print(f"[dim]Loading rosters {year} from cache...[/]")
                roster_year = pd.read_parquet(roster_cache)
            else:
                print(f"[bold]Loading rosters {year} from nflverse...[/]")
                roster_year = load_rosters([year])
                roster_year.to_parquet(roster_cache)
            
            # Load DST data
            if dst_weekly_cache.exists():
                print(f"[dim]Loading DST weekly {year} from cache...[/]")
                dst_weekly_year = pd.read_parquet(dst_weekly_cache)
            else:
                print(f"[bold]Loading DST weekly {year} from nflverse...[/]")
                dst_weekly_year = load_dst_weekly([year])
                dst_weekly_year.to_parquet(dst_weekly_cache)
            
            if dst_roster_cache.exists():
                print(f"[dim]Loading DST rosters {year} from cache...[/]")
                dst_roster_year = pd.read_parquet(dst_roster_cache)
            else:
                print(f"[bold]Loading DST rosters {year} from nflverse...[/]")
                dst_roster_year = load_dst_rosters([year])
                dst_roster_year.to_parquet(dst_roster_cache)
            
            # Load kicker data
            if kicker_weekly_cache.exists():
                print(f"[dim]Loading kicker weekly {year} from cache...[/]")
                kicker_weekly_year = pd.read_parquet(kicker_weekly_cache)
            else:
                print(f"[bold]Loading kicker weekly {year} from nflverse...[/]")
                kicker_weekly_year = load_kicker_weekly([year])
                kicker_weekly_year.to_parquet(kicker_weekly_cache)
            
            if kicker_roster_cache.exists():
                print(f"[dim]Loading kicker rosters {year} from cache...[/]")
                kicker_roster_year = pd.read_parquet(kicker_roster_cache)
            else:
                print(f"[bold]Loading kicker rosters {year} from nflverse...[/]")
                kicker_roster_year = load_kicker_rosters(year)
                kicker_roster_year.to_parquet(kicker_roster_cache)
        else:
            # No caching - load directly
            print(f"[bold]Loading weekly {year} from nflverse...[/]")
            weekly_year = load_weekly([year])
            print(f"[bold]Loading rosters {year} from nflverse...[/]")
            roster_year = load_rosters([year])
            print(f"[bold]Loading DST weekly {year} from nflverse...[/]")
            dst_weekly_year = load_dst_weekly([year])
            print(f"[bold]Loading DST rosters {year} from nflverse...[/]")
            dst_roster_year = load_dst_rosters([year])
            print(f"[bold]Loading kicker weekly {year} from nflverse...[/]")
            kicker_weekly_year = load_kicker_weekly([year])
            print(f"[bold]Loading kicker rosters {year} from nflverse...[/]")
            kicker_roster_year = load_kicker_rosters(year)
        
        weekly_frames.append(weekly_year)
        roster_frames.append(roster_year)
        dst_weekly_frames.append(dst_weekly_year)
        dst_roster_frames.append(dst_roster_year)
        kicker_weekly_frames.append(kicker_weekly_year)
        kicker_roster_frames.append(kicker_roster_year)
    
    # Combine all years
    weekly = pd.concat(weekly_frames, ignore_index=True) if weekly_frames else pd.DataFrame()
    rosters = pd.concat(roster_frames, ignore_index=True) if roster_frames else pd.DataFrame()
    dst_weekly = pd.concat(dst_weekly_frames, ignore_index=True) if dst_weekly_frames else pd.DataFrame()
    dst_rosters = pd.concat(dst_roster_frames, ignore_index=True) if dst_roster_frames else pd.DataFrame()
    kicker_weekly = pd.concat(kicker_weekly_frames, ignore_index=True) if kicker_weekly_frames else pd.DataFrame()
    kicker_rosters = pd.concat(kicker_roster_frames, ignore_index=True) if kicker_roster_frames else pd.DataFrame()
    
    return weekly, rosters, dst_weekly, dst_rosters, kicker_weekly, kicker_rosters

def add_snake_draft_helpers(players: list[dict], teams: int = 12) -> list[dict]:
    """Add round_est and pick_in_round to each player based on overall_rank."""
    for player in players:
        overall_rank = player.get('overall_rank', 0)
        if overall_rank > 0:
            player['round_est'] = ((overall_rank - 1) // teams) + 1
            player['pick_in_round'] = ((overall_rank - 1) % teams) + 1
        else:
            player['round_est'] = None
            player['pick_in_round'] = None
    return players

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
          min_games: int = typer.Option(8, "--min-games", help="Minimum games played in a season to include in projections"),
          onesie_discount: str = typer.Option("qb=0.90,te=1.00", "--onesie-discount", help="Position discount factors for single-starter positions (e.g., 'qb=0.90,te=1.00')"),
          cache: Path = typer.Option(None, "--cache", help="Cache directory for parquet files (speeds up rebuilds)")):
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

    # Parse onesie discount
    onesie_discounts = {}
    if onesie_discount:
        for pair in onesie_discount.split(','):
            if '=' in pair:
                pos_str, discount_str = pair.split('=', 1)
                pos = pos_str.strip().upper()
                discount = float(discount_str.strip())
                onesie_discounts[pos] = discount
        if onesie_discounts:
            print(f"[bold]Onesie discounts: {onesie_discounts}[/]")

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

    # 1) Load data (with caching if specified)
    if cache:
        print(f"[bold]Using cache directory: {cache}[/]")
        weekly, rosters, dst_weekly, dst_rosters, kicker_weekly, kicker_rosters = load_with_cache(data_years, cache)
    else:
        print(f"[bold]Loading nflverse data for {data_years} (no caching)...[/]")
        weekly, rosters, dst_weekly, dst_rosters, kicker_weekly, kicker_rosters = load_with_cache(data_years, None)
    
    print(f"[dim]Data loaded: {len(weekly)} weekly rows, {len(rosters)} roster rows, {len(dst_weekly)} DST weekly, {len(kicker_weekly)} kicker weekly[/]")

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
    all_players = compute_replacement_and_vorp(all_players, cfg, onesie_discounts)
    all_players = add_tiers_kmeans(all_players)

    # 5) Add snake-draft helpers
    print("[bold]Adding snake-draft helpers (round estimates)...[/]")
    all_players = add_snake_draft_helpers(all_players, teams=cfg.teams)

    # 6) Print diagnostics
    if year == 2025 and per_game:
        print_diagnostics(all_players, cfg)

    # 7) Export players.json
    outpath = outdir / "players.json"
    with outpath.open("w") as f:
        json.dump(all_players, f, indent=2)
    print(f"[green]Wrote {outpath}[/]")
    
    # 8) Export meta.json
    from datetime import datetime
    meta = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "target_year": year,
        "schema_version": "0.1.0"
    }
    
    if year == 2025 and per_game:
        meta.update({
            "lookback_years": data_years,
            "blend": blend_weights,
            "per_game": per_game,
            "min_games": min_games
        })
    
    meta_path = outdir / "meta.json"
    with meta_path.open("w") as f:
        json.dump(meta, f, indent=2)
    print(f"[green]Wrote {meta_path}[/]")

if __name__ == "__main__":
    app()
