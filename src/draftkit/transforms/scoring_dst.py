"""
DST (Defense/Special Teams) scoring for fantasy football.
Implements Yahoo-style tiered points-allowed scoring plus defensive stats.
"""
from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
import numpy as np

def _score_dst_row(row: Dict[str, Any], cfg) -> float:
    """Score a single DST row using league scoring settings."""
    points = 0.0
    
    # Defensive stats
    points += row.get('sacks', 0) * cfg.dst_sack
    points += row.get('interceptions', 0) * cfg.dst_int  
    points += row.get('fumble_recoveries', 0) * cfg.dst_fumble_recovery
    points += row.get('defensive_tds', 0) * cfg.dst_defensive_td
    points += row.get('safeties', 0) * cfg.dst_safety
    points += row.get('blocked_kicks', 0) * cfg.dst_blocked_kick
    
    # Points allowed bands (Yahoo style)
    points_allowed = row.get('points_allowed', 0)
    if points_allowed == 0:
        points += cfg.dst_points_allowed_0
    elif 1 <= points_allowed <= 6:
        points += cfg.dst_points_allowed_1_6
    elif 7 <= points_allowed <= 13:
        points += cfg.dst_points_allowed_7_13
    elif 14 <= points_allowed <= 20:
        points += cfg.dst_points_allowed_14_20
    elif 21 <= points_allowed <= 27:
        points += cfg.dst_points_allowed_21_27
    elif 28 <= points_allowed <= 34:
        points += cfg.dst_points_allowed_28_34
    else:  # 35+
        points += cfg.dst_points_allowed_35_plus
    
    return points

def apply_dst_scoring(dst_weekly: pd.DataFrame, dst_rosters: pd.DataFrame, cfg, bye_weeks: Dict[str, int] = None) -> List[Dict]:
    """
    Apply fantasy scoring to DST units for a single season.
    
    Args:
        dst_weekly: Weekly DST stats DataFrame
        dst_rosters: DST roster DataFrame  
        cfg: ScoringConfig with DST scoring settings
        bye_weeks: Dict mapping team -> bye week
        
    Returns:
        List of DST player dictionaries
    """
    if dst_weekly.empty or dst_rosters.empty:
        return []
    
    # Aggregate by team/season to get season totals
    agg_stats = dst_weekly.groupby(['team', 'season']).agg({
        'sacks': 'sum',
        'interceptions': 'sum', 
        'fumble_recoveries': 'sum',
        'defensive_tds': 'sum',
        'safeties': 'sum',
        'blocked_kicks': 'sum',
        'points_allowed': 'sum',
        'week': 'count'  # games played
    }).reset_index()
    
    agg_stats.rename(columns={'week': 'games'}, inplace=True)
    
    # Score each team
    agg_stats['points'] = agg_stats.apply(lambda r: _score_dst_row(r, cfg), axis=1)
    
    # Create DST players list
    dst_players = []
    for _, row in agg_stats.iterrows():
        team = row['team']
        
        dst_player = {
            'player_id': f'DEF-{team}',
            'name': f'{team} D/ST',
            'pos': 'DEF',
            'tm': team,
            'points': round(row['points'], 2)
        }
        
        # Add bye weeks if provided
        if bye_weeks and team in bye_weeks:
            dst_player['bye'] = bye_weeks[team]
            
        dst_players.append(dst_player)
    
    return dst_players

def apply_dst_blended_scoring(dst_weekly: pd.DataFrame, dst_rosters: pd.DataFrame, cfg, 
                             data_years: List[int], blend_weights: List[float], 
                             min_games: int = 8, bye_weeks: Dict[str, int] = None) -> List[Dict]:
    """
    Apply blended DST scoring across multiple seasons using per-game averages.
    
    Args:
        dst_weekly: Multi-season DST weekly stats
        dst_rosters: DST roster info
        cfg: ScoringConfig
        data_years: List of years in blend (e.g., [2024, 2023, 2022])
        blend_weights: Weights for each year (e.g., [0.6, 0.3, 0.1])
        min_games: Minimum games to include a team-season
        bye_weeks: Bye weeks for target year
        
    Returns:
        List of DST players with blended projections
    """
    if dst_weekly.empty:
        return []
    
    # Filter to specified years and calculate per-game averages by team/season
    dst_filtered = dst_weekly[dst_weekly['season'].isin(data_years)].copy()
    
    team_seasons = []
    for (team, season), group in dst_filtered.groupby(['team', 'season']):
        games_played = len(group)
        if games_played >= min_games:
            # Calculate per-game averages
            avg_stats = group.select_dtypes(include=['number']).mean()
            avg_stats['team'] = team
            avg_stats['season'] = season
            avg_stats['games_played'] = games_played
            team_seasons.append(avg_stats)
    
    if not team_seasons:
        return []
    
    per_game_df = pd.DataFrame(team_seasons)
    
    # Calculate blended projections for each team
    blended_teams = []
    for team in per_game_df['team'].unique():
        team_data = per_game_df[per_game_df['team'] == team].sort_values('season', ascending=False)
        
        # Initialize blended stats
        blended_stats = {'team': team}
        stat_cols = [col for col in team_data.columns if col not in ['team', 'season', 'games_played']]
        
        # Blend each stat using weights
        for stat in stat_cols:
            weighted_sum = 0
            total_weight = 0
            for i, (_, row) in enumerate(team_data.iterrows()):
                if i < len(blend_weights):
                    weight = blend_weights[i]
                    weighted_sum += row[stat] * weight
                    total_weight += weight
            
            if total_weight > 0:
                blended_stats[stat] = weighted_sum / total_weight
        
        blended_teams.append(blended_stats)
    
    if not blended_teams:
        return []
    
    blended_df = pd.DataFrame(blended_teams)
    
    # Project to full season (17 games)
    games_in_season = 17
    for col in blended_df.select_dtypes(include=['number']).columns:
        if col not in ['team', 'season']:
            blended_df[col] = blended_df[col] * games_in_season
    
    # Score DSTs
    blended_df['points'] = blended_df.apply(lambda r: _score_dst_row(r, cfg), axis=1)
    
    # Create DST players list
    dst_players = []
    for _, row in blended_df.iterrows():
        team = row['team']
        
        dst_player = {
            'player_id': f'DEF-{team}',
            'name': f'{team} D/ST',
            'pos': 'DEF', 
            'tm': team,
            'points': round(row['points'], 2)
        }
        
        # Add bye weeks if provided
        if bye_weeks and team in bye_weeks:
            dst_player['bye'] = bye_weeks[team]
            
        dst_players.append(dst_player)
    
    return dst_players
