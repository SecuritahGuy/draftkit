from __future__ import annotations
import pandas as pd
from nfl_data_py import importers as nfl

def load_weekly(years: list[int]) -> pd.DataFrame:
    # nfl.import_weekly_data returns weekly player stats across seasons
    df = nfl.import_weekly_data(years)
    # normalize some columns we care about
    needed = [
        'season','week','player_id','player_name','position','recent_team',
        'passing_yards','passing_tds','interceptions',
        'rushing_yards','rushing_tds',
        'receptions','receiving_yards','receiving_tds',
        'fumbles_lost','two_point_conversions'
    ]
    # Some columns might be missing in older seasons; fill if absent
    for col in needed:
        if col not in df.columns:
            df[col] = 0
    return df[needed].copy()

def load_rosters(years: list[int]) -> pd.DataFrame:
    rosters = nfl.import_rosters(years)
    keep = ['player_id','player_name','position','team','status']
    for col in keep:
        if col not in rosters.columns:
            rosters[col] = None
    return rosters[keep].drop_duplicates(subset=['player_id'])
