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

def apply_scoring(weekly: pd.DataFrame, rosters: pd.DataFrame, cfg: ScoringConfig) -> list[dict]:
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
    df = df[['player_id','name','pos','tm','points']].fillna({'points':0})
    # make list of dicts
    players = df.to_dict(orient='records')
    return players
