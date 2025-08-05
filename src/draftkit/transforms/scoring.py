from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd
import yaml

OFFENSE_POS = {'QB','RB','WR','TE'}

@dataclass
class ScoringConfig:
    # Passing
    pass_yds_per_pt: float = 25.0
    pass_td: float = 4.0
    interceptions: float = -2.0
    # Optional (rare in open data)
    pick_six_thrown: float = 0.0
    sacks_taken: float = 0.0
    # Rushing
    rush_yds_per_pt: float = 10.0
    rush_td: float = 6.0
    # Receiving
    rec: float = 1.0
    rec_yds_per_pt: float = 10.0
    rec_td: float = 6.0
    # Misc
    two_pt: float = 2.0
    fum_lost: float = -2.0
    # Roster/league settings for replacement
    teams: int = 12
    roster: Dict[str,int] = None  # e.g., {'QB':1,'RB':2,'WR':2,'TE':1,'FLEX':1,'K':1,'DEF':1}
    flex_positions: List[str] = None  # default ['RB','WR','TE']

    @staticmethod
    def from_yaml(path) -> 'ScoringConfig':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        s = data.get('scoring', {})
        roster = data.get('roster', {'QB':1,'RB':2,'WR':2,'TE':1,'FLEX':1,'K':1,'DEF':1})
        teams = int(data.get('teams', 12))
        flex_positions = data.get('flex_positions', ['RB','WR','TE'])
        return ScoringConfig(
            pass_yds_per_pt=s.get('passYdsPerPt',25),
            pass_td=s.get('passTd',4),
            interceptions=s.get('int',-2),
            pick_six_thrown=s.get('pickSixThrown',0),
            sacks_taken=s.get('sackTaken',0),
            rush_yds_per_pt=s.get('rushYdsPerPt',10),
            rush_td=s.get('rushTd',6),
            rec=s.get('rec',1),
            rec_yds_per_pt=s.get('recYdsPerPt',10),
            rec_td=s.get('recTd',6),
            two_pt=s.get('twoPt',2),
            fum_lost=s.get('fumLost',-2),
            teams=teams,
            roster=roster,
            flex_positions=flex_positions
        )

def _score_row(row, cfg: ScoringConfig) -> float:
    pts = 0.0
    pts += row.get('passing_yards',0) / cfg.pass_yds_per_pt + row.get('passing_tds',0) * cfg.pass_td
    pts += row.get('interceptions',0) * cfg.interceptions
    pts += row.get('rushing_yards',0) / cfg.rush_yds_per_pt + row.get('rushing_tds',0) * cfg.rush_td
    pts += row.get('receptions',0) * cfg.rec + row.get('receiving_yards',0) / cfg.rec_yds_per_pt + row.get('receiving_tds',0) * cfg.rec_td
    pts += row.get('two_point_conversions',0) * cfg.two_pt + row.get('fumbles_lost',0) * cfg.fum_lost
    return round(pts, 2)

def apply_blended_scoring(weekly: pd.DataFrame, rosters: pd.DataFrame, cfg: ScoringConfig, 
                         data_years: list[int], blend_weights: list[float], min_games: int, 
                         bye_weeks: dict[str, int] = None) -> list[dict]:
    """
    Apply blended per-game scoring using historical data.
    
    Args:
        weekly: Weekly stats dataframe with 'season' column
        rosters: Roster dataframe  
        cfg: Scoring configuration
        data_years: Years to blend (most recent first)
        blend_weights: Weights for each year (most recent first)
        min_games: Minimum games to include a player-season
    
    Returns:
        List of player dictionaries with blended projections
    """
    # Get base roster info
    base = rosters[['player_id','player_name','position','team']].drop_duplicates('player_id')
    
    # Calculate per-game stats for each year
    yearly_ppg = {}
    for year in data_years:
        year_data = weekly[weekly['season'] == year].copy()
        if year_data.empty:
            continue
            
        # Aggregate to season totals and game counts
        agg = year_data.groupby('player_id').agg({
            'passing_yards': 'sum',
            'passing_tds': 'sum', 
            'interceptions': 'sum',
            'rushing_yards': 'sum',
            'rushing_tds': 'sum',
            'receptions': 'sum',
            'receiving_yards': 'sum',
            'receiving_tds': 'sum',
            'two_point_conversions': 'sum',
            'fumbles_lost': 'sum',
            'week': 'count'  # games played
        }).reset_index()
        agg.rename(columns={'week': 'games'}, inplace=True)
        
        # Filter by minimum games
        agg = agg[agg['games'] >= min_games].copy()
        
        # Calculate total points and PPG
        agg['points'] = agg.apply(lambda r: _score_row(r, cfg), axis=1)
        agg['ppg'] = agg['points'] / agg['games']
        
        yearly_ppg[year] = agg[['player_id', 'ppg', 'games']].copy()
    
    # Blend PPG across years for each player
    all_players = set()
    for year_data in yearly_ppg.values():
        all_players.update(year_data['player_id'].tolist())
    
    blended_projections = []
    for player_id in all_players:
        weighted_ppg = 0.0
        total_weight = 0.0
        player_data = {}
        
        # Blend PPG across available years
        for i, year in enumerate(data_years):
            if year in yearly_ppg:
                year_data = yearly_ppg[year]
                player_year = year_data[year_data['player_id'] == player_id]
                if not player_year.empty:
                    ppg = player_year.iloc[0]['ppg']
                    weight = blend_weights[i]
                    weighted_ppg += ppg * weight
                    total_weight += weight
                    if not player_data:  # Store first found data for games reference
                        player_data = player_year.iloc[0].to_dict()
        
        if total_weight > 0:
            # Normalize by actual weights used
            final_ppg = weighted_ppg / total_weight
            # Project to 17-game season
            projected_points = final_ppg * 17
            
            blended_projections.append({
                'player_id': player_id,
                'projected_ppg': round(final_ppg, 2),
                'projected_points': round(projected_points, 2)
            })
    
    # Merge with roster data
    blend_df = pd.DataFrame(blended_projections)
    df = base.merge(blend_df, on='player_id', how='inner')
    
    # Keep offense for v0  
    df = df[df['position'].isin(OFFENSE_POS)].copy()
    
    # Format output
    df['name'] = df['player_name']
    df['pos'] = df['position'] 
    df['tm'] = df['team']
    df['points'] = df['projected_points']
    
    # Add bye weeks if provided
    if bye_weeks:
        df['bye'] = df['tm'].map(bye_weeks).fillna(0).astype(int)
        output_cols = ['player_id','name','pos','tm','points','bye']
    else:
        output_cols = ['player_id','name','pos','tm','points']
    
    df = df[output_cols].fillna({'points':0})
    
    # Convert to list of dicts
    players = df.to_dict(orient='records')
    return players


def apply_scoring(weekly: pd.DataFrame, rosters: pd.DataFrame, cfg: ScoringConfig, 
                 bye_weeks: dict[str, int] = None) -> list[dict]:
    # aggregate to season totals
    agg = weekly.groupby('player_id', as_index=False).sum(numeric_only=True)
    # join back names/pos/team (prefer rosters)
    base = rosters[['player_id','player_name','position','team']].drop_duplicates('player_id')
    df = base.merge(agg, on='player_id', how='left')
    # score
    df['points'] = df.apply(lambda r: _score_row(r, cfg), axis=1)
    # keep offense for v0
    df = df[df['position'].isin(OFFENSE_POS)].copy()
    # basic fields
    df['name'] = df['player_name']
    df['pos'] = df['position']
    df['tm'] = df['team']
    
    # Add bye weeks if provided
    if bye_weeks:
        df['bye'] = df['tm'].map(bye_weeks).fillna(0).astype(int)
        output_cols = ['player_id','name','pos','tm','points','bye']
    else:
        output_cols = ['player_id','name','pos','tm','points']
    
    df = df[output_cols].fillna({'points':0})
    # make list of dicts
    players = df.to_dict(orient='records')
    return players
