"""
Kicker scoring for fantasy football.
Supports distance-based field goal scoring with fallback to flat rates.
"""
from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
import numpy as np

def _score_kicker_row(row: Dict[str, Any], cfg) -> float:
    """Score a single kicker row using league scoring settings."""
    points = 0.0
    
    # Distance-based field goals (if available)
    if hasattr(cfg, 'k_fg_0_39') and 'fg_0_39' in row:
        points += row.get('fg_0_39', 0) * cfg.k_fg_0_39
        points += row.get('fg_40_49', 0) * cfg.k_fg_40_49  
        points += row.get('fg_50_plus', 0) * cfg.k_fg_50_plus
    else:
        # Fallback to flat field goal rate
        total_fgs = row.get('fg_made', 0)
        points += total_fgs * getattr(cfg, 'k_fg_flat', 3)
    
    # Extra points
    points += row.get('xp_made', 0) * cfg.k_xp
    
    # Penalties (usually 0)
    points += row.get('fg_miss', 0) * cfg.k_fg_miss
    points += row.get('xp_miss', 0) * cfg.k_xp_miss
    
    return points

def apply_kicker_scoring(kicker_weekly: pd.DataFrame, kicker_rosters: pd.DataFrame, cfg, bye_weeks: Dict[str, int] = None) -> List[Dict]:
    """
    Apply fantasy scoring to kickers for a single season.
    
    Args:
        kicker_weekly: Weekly kicker stats DataFrame
        kicker_rosters: Kicker roster DataFrame  
        cfg: ScoringConfig with kicker scoring settings
        bye_weeks: Dict mapping team -> bye week
        
    Returns:
        List of kicker player dictionaries
    """
    if kicker_weekly.empty or kicker_rosters.empty:
        return []
    
    # Aggregate by player/season to get season totals
    agg_stats = kicker_weekly.groupby(['player_display_name', 'player_id', 'team', 'season']).agg({
        'fg_0_39': 'sum',
        'fg_40_49': 'sum', 
        'fg_50_plus': 'sum',
        'xp_made': 'sum',
        'fg_miss': 'sum',
        'xp_miss': 'sum',
        'week': 'count'  # games played
    }).reset_index()
    
    agg_stats.rename(columns={'week': 'games'}, inplace=True)
    
    # Score each kicker
    agg_stats['points'] = agg_stats.apply(lambda r: _score_kicker_row(r, cfg), axis=1)
    
    # Get most recent roster info for display names  
    current_season = agg_stats['season'].max()
    current_rosters = kicker_rosters[kicker_rosters['season'] == current_season].copy()
    
    # Join with roster data
    df = current_rosters.merge(agg_stats, on=['player_id', 'team'], how='left')
    
    # Create kicker players list
    kicker_players = []
    for _, row in df.iterrows():
        if pd.isna(row['points']):
            continue  # Skip kickers with no stats
            
        kicker_player = {
            'player_id': row['player_id'],
            'name': row['player_display_name'],  # Use full name from weekly data
            'pos': 'K',
            'tm': row['team'], 
            'points': round(row['points'], 2)
        }
        
        # Add bye weeks if provided
        if bye_weeks and row['team'] in bye_weeks:
            kicker_player['bye'] = bye_weeks[row['team']]
            
        kicker_players.append(kicker_player)
    
    return kicker_players

def apply_kicker_blended_scoring(kicker_weekly: pd.DataFrame, kicker_rosters: pd.DataFrame, cfg, 
                                data_years: List[int], blend_weights: List[float], 
                                min_games: int = 8, bye_weeks: Dict[str, int] = None) -> List[Dict]:
    """
    Apply blended kicker scoring across multiple seasons using per-game averages.
    
    Args:
        kicker_weekly: Multi-season kicker weekly stats
        kicker_rosters: Kicker roster info
        cfg: ScoringConfig
        data_years: List of years in blend (e.g., [2024, 2023, 2022])
        blend_weights: Weights for each year (e.g., [0.6, 0.3, 0.1])
        min_games: Minimum games to include a player-season
        bye_weeks: Bye weeks for target year
        
    Returns:
        List of kicker players with blended projections
    """
    if kicker_weekly.empty:
        return []
    
    # Filter to specified years and calculate per-game averages by player/season
    kicker_filtered = kicker_weekly[kicker_weekly['season'].isin(data_years)].copy()
    
    player_seasons = []
    for (player, player_id, team, season), group in kicker_filtered.groupby(['player_display_name', 'player_id', 'team', 'season']):
        games_played = len(group)
        if games_played >= min_games:
            # Calculate per-game averages
            avg_stats = group.select_dtypes(include=['number']).mean()
            avg_stats['player_display_name'] = player
            avg_stats['player_id'] = player_id
            avg_stats['team'] = team
            avg_stats['season'] = season
            avg_stats['games_played'] = games_played
            player_seasons.append(avg_stats)
    
    if not player_seasons:
        return []
    
    per_game_df = pd.DataFrame(player_seasons)
    
    # Calculate blended projections for each player
    blended_players = []
    for player in per_game_df['player_display_name'].unique():
        player_data = per_game_df[per_game_df['player_display_name'] == player].sort_values('season', ascending=False)
        
        # Get most recent team
        most_recent_team = player_data.iloc[0]['team']
        
        # Initialize blended stats
        blended_stats = {'player_display_name': player, 'player_id': player_data.iloc[0]['player_id'], 'team': most_recent_team}
        stat_cols = [col for col in player_data.columns if col not in ['player_display_name', 'player_id', 'team', 'season', 'games_played']]
        
        # Blend each stat using weights
        for stat in stat_cols:
            weighted_sum = 0
            total_weight = 0
            for i, (_, row) in enumerate(player_data.iterrows()):
                if i < len(blend_weights):
                    weight = blend_weights[i]
                    weighted_sum += row[stat] * weight
                    total_weight += weight
            
            if total_weight > 0:
                blended_stats[stat] = weighted_sum / total_weight
        
        blended_players.append(blended_stats)
    
    if not blended_players:
        return []
    
    blended_df = pd.DataFrame(blended_players)
    
    # Project to full season (17 games)
    games_in_season = 17
    for col in blended_df.select_dtypes(include=['number']).columns:
        if col not in ['player_display_name', 'player_id', 'team', 'season']:
            blended_df[col] = blended_df[col] * games_in_season
    
    # Get most recent roster info
    current_season = max(data_years)
    current_rosters = kicker_rosters.copy()
    
    # Join with roster data
    df = current_rosters.merge(blended_df, on=['player_id', 'team'], how='left')
    
    # Score kickers
    df['points'] = df.apply(lambda r: _score_kicker_row(r, cfg), axis=1)
    
    # Basic fields - use roster name (full name) as primary
    df['name'] = df['player_display_name_x']  # Roster name (full name)
    df['pos'] = df['position']
    df['tm'] = df['team']
    
    # Add bye weeks if provided
    if bye_weeks:
        df['bye'] = df['tm'].map(bye_weeks).fillna(0).astype(int)
        output_cols = ['name', 'pos', 'tm', 'points', 'bye']
    else:
        output_cols = ['name', 'pos', 'tm', 'points']
    
    df = df[output_cols].fillna({'points': 0})
    
    # Make list of dicts
    kicker_players = df.to_dict(orient='records')
    return kicker_players
