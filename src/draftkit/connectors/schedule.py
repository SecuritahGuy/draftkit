from __future__ import annotations
import pandas as pd
import nfl_data_py as nfl

def load_bye_weeks(year: int) -> dict[str, int]:
    """
    Load bye weeks for all teams in a given year.
    
    Args:
        year: Season year to get bye weeks for
        
    Returns:
        Dictionary mapping team abbreviation to bye week number
    """
    # Get schedule for the year
    sched = nfl.import_schedules([year])
    
    # Filter to regular season only  
    regular_season = sched[sched['game_type'] == 'REG'].copy()
    
    # Get all teams
    all_teams = set(regular_season['home_team'].unique()) | set(regular_season['away_team'].unique())
    
    # Find bye weeks - teams that don't play in a given week
    bye_weeks = {}
    for week in sorted(regular_season['week'].unique()):
        week_games = regular_season[regular_season['week'] == week]
        playing_teams = set(week_games['home_team'].unique()) | set(week_games['away_team'].unique())
        bye_teams = all_teams - playing_teams
        
        for team in bye_teams:
            bye_weeks[team] = week
    
    return bye_weeks

def get_2025_bye_weeks() -> dict[str, int]:
    """
    Get projected 2025 bye weeks.
    
    Since 2025 schedule isn't available, use 2024 bye weeks as approximation.
    In practice, you'd want to update this when the 2025 schedule is released.
    
    Returns:
        Dictionary mapping team abbreviation to bye week number  
    """
    # Use 2024 bye weeks as approximation for 2025
    return load_bye_weeks(2024)
