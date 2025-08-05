"""
Kicker data loading from nflverse play-by-play data.

Loads field goal and extra point attempts/makes for fantasy kicker scoring.
"""

import pandas as pd
import nfl_data_py as nfl
from typing import List, Dict, Any


def load_kicker_weekly(years: List[int]) -> pd.DataFrame:
    """
    Load weekly kicker statistics from play-by-play data.
    
    Args:
        years: List of NFL seasons (e.g., [2023, 2024])
        
    Returns:
        DataFrame with columns:
        - season: NFL season year
        - week: Week number
        - player_display_name: Kicker name
        - team: Team abbreviation
        - fg_0_39: Field goals made 0-39 yards
        - fg_40_49: Field goals made 40-49 yards
        - fg_50_plus: Field goals made 50+ yards
        - xp_made: Extra points made
        - fg_miss: Field goals missed (for potential future scoring)
        - xp_miss: Extra points missed (for potential future scoring)
    """
    if not years:
        return pd.DataFrame()
    
    print(f"Loading kicker data for years: {years}")
    
    try:
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, cache=False)
        
        # Filter to kicking plays only
        kick_plays = pbp[pbp['play_type'].isin(['field_goal', 'extra_point'])].copy()
        
        if kick_plays.empty:
            print("Warning: No kicking plays found in data")
            return pd.DataFrame()
        
        # Process field goals
        fg_plays = kick_plays[kick_plays['play_type'] == 'field_goal'].copy()
        
        # Create distance buckets for field goals
        fg_plays['distance_bucket'] = pd.cut(
            fg_plays['kick_distance'], 
            bins=[0, 39, 49, float('inf')], 
            labels=['0_39', '40_49', '50_plus'],
            include_lowest=True
        )
        
        # Aggregate field goals by kicker, week, and distance bucket
        fg_made = fg_plays[fg_plays['field_goal_result'] == 'made'].copy()
        fg_miss = fg_plays[fg_plays['field_goal_result'].isin(['missed', 'blocked'])].copy()
        
        # Group successful field goals by distance bucket
        fg_stats = []
        for bucket in ['0_39', '40_49', '50_plus']:
            bucket_made = fg_made[fg_made['distance_bucket'] == bucket].groupby([
                'season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'
            ]).size().reset_index(name=f'fg_{bucket}')
            fg_stats.append(bucket_made)
        
        # Merge field goal distance buckets
        kicker_fg = fg_stats[0]
        for bucket_df in fg_stats[1:]:
            kicker_fg = kicker_fg.merge(
                bucket_df, 
                on=['season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'], 
                how='outer'
            )
        
        # Add field goal misses
        fg_miss_stats = fg_miss.groupby([
            'season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'
        ]).size().reset_index(name='fg_miss')
        
        if not fg_miss_stats.empty:
            kicker_fg = kicker_fg.merge(
                fg_miss_stats,
                on=['season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'],
                how='outer'
            )
        else:
            kicker_fg['fg_miss'] = 0
        
        # Process extra points
        xp_plays = kick_plays[kick_plays['play_type'] == 'extra_point'].copy()
        
        xp_made = xp_plays[xp_plays['extra_point_result'] == 'good'].groupby([
            'season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'
        ]).size().reset_index(name='xp_made')
        
        xp_miss = xp_plays[xp_plays['extra_point_result'].isin(['failed', 'blocked'])].groupby([
            'season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'
        ]).size().reset_index(name='xp_miss')
        
        # Merge all kicker stats
        kicker_stats = kicker_fg.merge(
            xp_made, 
            on=['season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'], 
            how='outer'
        )
        
        if not xp_miss.empty:
            kicker_stats = kicker_stats.merge(
                xp_miss,
                on=['season', 'week', 'kicker_player_name', 'kicker_player_id', 'posteam'],
                how='outer'
            )
        else:
            kicker_stats['xp_miss'] = 0
        
        # Fill NaN values with 0
        stat_cols = ['fg_0_39', 'fg_40_49', 'fg_50_plus', 'xp_made', 'fg_miss', 'xp_miss']
        for col in stat_cols:
            if col in kicker_stats.columns:
                kicker_stats[col] = kicker_stats[col].fillna(0).astype(int)
            else:
                kicker_stats[col] = 0
        
        # Rename columns to match expected format
        kicker_stats = kicker_stats.rename(columns={
            'kicker_player_name': 'player_display_name',
            'kicker_player_id': 'player_id',
            'posteam': 'team'
        })
        
        # Ensure we have all required columns
        required_cols = ['season', 'week', 'player_display_name', 'player_id', 'team'] + stat_cols
        for col in required_cols:
            if col not in kicker_stats.columns:
                kicker_stats[col] = 0
        
        print(f"Loaded {len(kicker_stats)} kicker-week records")
        return kicker_stats[required_cols]
        
    except Exception as e:
        print(f"Error loading kicker data: {e}")
        return pd.DataFrame()


def load_kicker_rosters(year: int) -> pd.DataFrame:
    """
    Load current season kicker rosters for projection.
    
    Args:
        year: Target season for projections
        
    Returns:
        DataFrame with kicker roster information
    """
    try:
        # Load roster data
        rosters = nfl.import_seasonal_rosters([year])
        kickers = rosters[rosters['position'] == 'K'].copy()
        
        if kickers.empty:
            print(f"Warning: No kickers found in {year} roster data")
            return pd.DataFrame()
        
        # Select relevant columns
        kicker_roster = kickers[[
            'player_name', 'player_id', 'team', 'position'
        ]].copy()
        
        # Rename to match expected format from weekly data
        kicker_roster = kicker_roster.rename(columns={
            'player_name': 'player_display_name'
        })
        
        print(f"Loaded {len(kicker_roster)} kickers for {year}")
        return kicker_roster
        
    except Exception as e:
        print(f"Error loading kicker rosters: {e}")
        return pd.DataFrame()
