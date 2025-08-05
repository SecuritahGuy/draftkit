"""
DST (Defense/Special Teams) data connector for fantasy football scoring.

This module aggregates team-level defensive stats from various NFL data sources.
"""
import pandas as pd
import nfl_data_py as nfl
from typing import List

def load_dst_weekly(years: List[int]) -> pd.DataFrame:
    """
    Load weekly DST stats aggregated by team.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with columns: team, season, week, points_allowed, sacks, interceptions,
        fumble_recoveries, defensive_tds, safeties, blocked_kicks
    """
    
    # Load individual defensive player stats
    def_stats = nfl.import_weekly_pfr('def', years)
    
    # Aggregate defensive stats by team/week/season
    team_def_stats = def_stats.groupby(['team', 'season', 'week']).agg({
        'def_sacks': 'sum',
        'def_ints': 'sum',
        'def_tackles_combined': 'sum'  # Could be useful for IDP leagues later
    }).reset_index()
    
    # Load schedules to get team scores (points allowed)
    schedules = nfl.import_schedules(years)
    
    # Filter to regular season games only
    schedules = schedules[schedules['game_type'] == 'REG'].copy()
    
    # Calculate points allowed for each team from schedule data
    points_allowed = []
    
    for _, game in schedules.iterrows():
        # Skip games without scores (future games, etc.)
        if pd.isna(game['home_score']) or pd.isna(game['away_score']):
            continue
            
        # Home team allowed away team's score
        points_allowed.append({
            'team': game['home_team'],
            'season': game['season'], 
            'week': game['week'],
            'points_allowed': game['away_score']
        })
        
        # Away team allowed home team's score  
        points_allowed.append({
            'team': game['away_team'],
            'season': game['season'],
            'week': game['week'], 
            'points_allowed': game['home_score']
        })
    
    points_df = pd.DataFrame(points_allowed)
    
    # For now, set other advanced DST stats to 0 since extracting them is complex
    # These can be enhanced later with more detailed PBP analysis
    if not points_df.empty:
        points_df['fumble_recoveries'] = 0  # TODO: Extract from PBP
        points_df['defensive_tds'] = 0      # TODO: Extract from PBP  
        points_df['safeties'] = 0           # TODO: Extract from PBP
        points_df['blocked_kicks'] = 0      # TODO: Extract from PBP
    
    # Merge team defensive stats with points allowed
    if not team_def_stats.empty and not points_df.empty:
        result = team_def_stats.merge(
            points_df, 
            on=['team', 'season', 'week'], 
            how='outer'
        )
    elif not team_def_stats.empty:
        result = team_def_stats.copy()
        result['points_allowed'] = 0
        result['fumble_recoveries'] = 0
        result['defensive_tds'] = 0
        result['safeties'] = 0
        result['blocked_kicks'] = 0
    elif not points_df.empty:
        result = points_df.copy()
        result['def_sacks'] = 0
        result['def_ints'] = 0
        result['def_tackles_combined'] = 0
    else:
        # No data available, return empty DataFrame with expected structure
        return pd.DataFrame(columns=[
            'team', 'season', 'week', 'points_allowed', 'sacks', 'interceptions',
            'fumble_recoveries', 'defensive_tds', 'safeties', 'blocked_kicks'
        ])
    
    # Fill missing values with 0
    result = result.fillna(0)
    
    # Rename columns to match standard naming
    result = result.rename(columns={
        'def_sacks': 'sacks',
        'def_ints': 'interceptions'
    })
    
    # Ensure we have the expected columns
    expected_columns = [
        'team', 'season', 'week', 'points_allowed', 'sacks', 'interceptions',
        'fumble_recoveries', 'defensive_tds', 'safeties', 'blocked_kicks'
    ]
    
    for col in expected_columns:
        if col not in result.columns:
            result[col] = 0
    
    # Ensure data types are correct
    for col in ['points_allowed', 'sacks', 'interceptions', 'fumble_recoveries', 
               'defensive_tds', 'safeties', 'blocked_kicks']:
        result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
    
    return result[expected_columns]


def load_dst_rosters(years: List[int]) -> pd.DataFrame:
    """
    Create DST roster data for fantasy purposes.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with DST team entries formatted like player rosters
    """
    
    # Get list of teams from schedules
    schedules = nfl.import_schedules(years)
    teams = set()
    teams.update(schedules['home_team'].unique())
    teams.update(schedules['away_team'].unique())
    
    # Create DST roster entries for each team/year
    dst_rosters = []
    for year in years:
        for team in teams:
            dst_rosters.append({
                'player_id': f'{team}_DST_{year}',
                'player_name': f'{team} DST',
                'position': 'DST',
                'team': team,
                'season': year
            })
    
    return pd.DataFrame(dst_rosters)
