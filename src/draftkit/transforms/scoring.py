from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd
import yaml

OFFENSE_POS = {'QB','RB','WR','TE'}
DST_POS = {'DST'}
KICKER_POS = {'K'}

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
    # DST/Defense Scoring
    dst_sack: float = 1.0
    dst_int: float = 2.0
    dst_fumble_recovery: float = 2.0
    dst_defensive_td: float = 6.0
    dst_safety: float = 2.0
    dst_blocked_kick: float = 2.0
    # Points allowed scoring (tiered)
    dst_points_allowed_0: float = 10.0        # 0 points allowed
    dst_points_allowed_1_6: float = 7.0       # 1-6 points allowed
    dst_points_allowed_7_13: float = 4.0      # 7-13 points allowed
    dst_points_allowed_14_20: float = 1.0     # 14-20 points allowed
    dst_points_allowed_21_27: float = 0.0     # 21-27 points allowed
    dst_points_allowed_28_34: float = -1.0    # 28-34 points allowed
    dst_points_allowed_35_plus: float = -4.0  # 35+ points allowed
    # Kicker Scoring
    k_fg_0_39: float = 3.0                    # Field goals 0-39 yards
    k_fg_40_49: float = 4.0                   # Field goals 40-49 yards
    k_fg_50_plus: float = 5.0                 # Field goals 50+ yards
    k_xp: float = 1.0                         # Extra points
    k_fg_miss: float = 0.0                    # Missed field goals (optional penalty)
    k_xp_miss: float = 0.0                    # Missed extra points (optional penalty)
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
            # DST scoring
            dst_sack=s.get('dstSack',1),
            dst_int=s.get('dstInt',2),
            dst_fumble_recovery=s.get('dstFumbleRecovery',2),
            dst_defensive_td=s.get('dstDefensiveTd',6),
            dst_safety=s.get('dstSafety',2),
            dst_blocked_kick=s.get('dstBlockedKick',2),
            dst_points_allowed_0=s.get('dstPointsAllowed0',10),
            dst_points_allowed_1_6=s.get('dstPointsAllowed1_6',7),
            dst_points_allowed_7_13=s.get('dstPointsAllowed7_13',4),
            dst_points_allowed_14_20=s.get('dstPointsAllowed14_20',1),
            dst_points_allowed_21_27=s.get('dstPointsAllowed21_27',0),
            dst_points_allowed_28_34=s.get('dstPointsAllowed28_34',-1),
            dst_points_allowed_35_plus=s.get('dstPointsAllowed35Plus',-4),
            # Kicker scoring
            k_fg_0_39=s.get('kFg0_39',3),
            k_fg_40_49=s.get('kFg40_49',4),
            k_fg_50_plus=s.get('kFg50Plus',5),
            k_xp=s.get('kXp',1),
            k_fg_miss=s.get('kFgMiss',0),
            k_xp_miss=s.get('kXpMiss',0),
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

def _score_dst_row(row, cfg: ScoringConfig) -> float:
    """Score a DST row based on team defensive stats."""
    pts = 0.0
    
    # Basic defensive stats
    pts += row.get('sacks', 0) * cfg.dst_sack
    pts += row.get('interceptions', 0) * cfg.dst_int
    pts += row.get('fumble_recoveries', 0) * cfg.dst_fumble_recovery
    pts += row.get('defensive_tds', 0) * cfg.dst_defensive_td
    pts += row.get('safeties', 0) * cfg.dst_safety
    pts += row.get('blocked_kicks', 0) * cfg.dst_blocked_kick
    
    # Points allowed (tiered scoring)
    points_allowed = row.get('points_allowed', 0)
    if points_allowed == 0:
        pts += cfg.dst_points_allowed_0
    elif points_allowed <= 6:
        pts += cfg.dst_points_allowed_1_6
    elif points_allowed <= 13:
        pts += cfg.dst_points_allowed_7_13
    elif points_allowed <= 20:
        pts += cfg.dst_points_allowed_14_20
    elif points_allowed <= 27:
        pts += cfg.dst_points_allowed_21_27
    elif points_allowed <= 34:
        pts += cfg.dst_points_allowed_28_34
    else:  # 35+
        pts += cfg.dst_points_allowed_35_plus
    
    return round(pts, 2)

def _score_kicker_row(row, cfg: ScoringConfig) -> float:
    """Score a kicker row based on field goals and extra points."""
    pts = 0.0
    
    # Field goals by distance
    pts += row.get('fg_0_39', 0) * cfg.k_fg_0_39
    pts += row.get('fg_40_49', 0) * cfg.k_fg_40_49
    pts += row.get('fg_50_plus', 0) * cfg.k_fg_50_plus
    
    # Extra points
    pts += row.get('xp_made', 0) * cfg.k_xp
    
    # Optional penalties for misses (usually 0)
    pts += row.get('fg_miss', 0) * cfg.k_fg_miss
    pts += row.get('xp_miss', 0) * cfg.k_xp_miss
    
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


def apply_dst_scoring(dst_weekly: pd.DataFrame, dst_rosters: pd.DataFrame, cfg: ScoringConfig,
                     bye_weeks: dict[str, int] = None) -> list[dict]:
    """
    Apply fantasy scoring to DST weekly data.
    
    Args:
        dst_weekly: Weekly DST stats DataFrame
        dst_rosters: DST roster DataFrame
        cfg: Scoring configuration
        bye_weeks: Dict mapping team abbreviation to bye week
        
    Returns:
        List of DST players with fantasy points
    """
    # Aggregate DST stats to season totals
    agg = dst_weekly.groupby(['team', 'season'], as_index=False).sum(numeric_only=True)
    
    # Join with roster data to get player info
    base = dst_rosters[['player_id', 'player_name', 'position', 'team', 'season']].drop_duplicates(['team', 'season'])
    df = base.merge(agg, on=['team', 'season'], how='left')
    
    # Score DST units
    df['points'] = df.apply(lambda r: _score_dst_row(r, cfg), axis=1)
    
    # Basic fields
    df['name'] = df['player_name']
    df['pos'] = df['position']
    df['tm'] = df['team']
    
    # Add bye weeks if provided
    if bye_weeks:
        df['bye'] = df['tm'].map(bye_weeks).fillna(0).astype(int)
        output_cols = ['player_id', 'name', 'pos', 'tm', 'points', 'bye']
    else:
        output_cols = ['player_id', 'name', 'pos', 'tm', 'points']
    
    df = df[output_cols].fillna({'points': 0})
    
    # Make list of dicts
    dst_players = df.to_dict(orient='records')
    return dst_players


def apply_dst_blended_scoring(dst_weekly: pd.DataFrame, dst_rosters: pd.DataFrame, cfg: ScoringConfig,
                             data_years: list[int], blend_weights: list[float], min_games: int,
                             bye_weeks: dict[str, int] = None) -> list[dict]:
    """
    Apply blended per-game scoring to DST data using historical data.
    
    Args:
        dst_weekly: Weekly DST stats DataFrame with 'season' column
        dst_rosters: DST roster DataFrame
        cfg: Scoring configuration
        data_years: Years to blend (most recent first)
        blend_weights: Weights for each year (most recent first)  
        min_games: Minimum games to include a team-season
        bye_weeks: Dict mapping team abbreviation to bye week
        
    Returns:
        List of DST players with blended fantasy points projections
    """
    # Filter years and calculate per-game averages
    dst_filtered = dst_weekly[dst_weekly['season'].isin(data_years)].copy()
    
    # Group by team/season and calculate per-game averages
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
    
    # Calculate blended projections
    blended_teams = []
    for team in per_game_df['team'].unique():
        team_data = per_game_df[per_game_df['team'] == team].copy()
        team_data = team_data.sort_values('season', ascending=False)  # Most recent first
        
        if len(team_data) == 0:
            continue
            
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
    
    # Get most recent roster info
    current_season = max(data_years)
    current_rosters = dst_rosters[dst_rosters['season'] == current_season].copy()
    
    # Join with roster data
    df = current_rosters.merge(blended_df, on='team', how='left')
    
    # Score DST units
    df['points'] = df.apply(lambda r: _score_dst_row(r, cfg), axis=1)
    
    # Basic fields
    df['name'] = df['player_name']
    df['pos'] = df['position']
    df['tm'] = df['team']
    
    # Add bye weeks if provided
    if bye_weeks:
        df['bye'] = df['tm'].map(bye_weeks).fillna(0).astype(int)
        output_cols = ['player_id', 'name', 'pos', 'tm', 'points', 'bye']
    else:
        output_cols = ['player_id', 'name', 'pos', 'tm', 'points']
    
    df = df[output_cols].fillna({'points': 0})
    
    # Make list of dicts
    dst_players = df.to_dict(orient='records')
    return dst_players


def apply_kicker_scoring(kicker_weekly: pd.DataFrame, kicker_rosters: pd.DataFrame, cfg: ScoringConfig,
                        bye_weeks: dict[str, int] = None) -> list[dict]:
    """
    Apply fantasy scoring to kicker weekly data.
    
    Args:
        kicker_weekly: Weekly kicker stats DataFrame
        kicker_rosters: Kicker roster DataFrame
        cfg: Scoring configuration
        bye_weeks: Dict mapping team abbreviation to bye week
        
    Returns:
        List of kicker players with fantasy points
    """
    # Aggregate kicker stats to season totals
    agg = kicker_weekly.groupby(['player_display_name', 'player_id', 'team', 'season'], as_index=False).sum(numeric_only=True)
    
    # Join with roster data to get player info
    df = kicker_rosters.merge(agg, on=['player_id', 'team'], how='left')
    
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


def apply_kicker_blended_scoring(kicker_weekly: pd.DataFrame, kicker_rosters: pd.DataFrame, cfg: ScoringConfig,
                                data_years: list[int], blend_weights: list[float], min_games: int,
                                bye_weeks: dict[str, int] = None) -> list[dict]:
    """
    Apply blended per-game scoring to kicker data using historical data.
    
    Args:
        kicker_weekly: Weekly kicker stats DataFrame with 'season' column
        kicker_rosters: Kicker roster DataFrame
        cfg: Scoring configuration
        data_years: Years to blend (most recent first)
        blend_weights: Weights for each year (most recent first)  
        min_games: Minimum games to include a player-season
        bye_weeks: Dict mapping team abbreviation to bye week
        
    Returns:
        List of kicker players with blended fantasy points projections
    """
    # Filter years and calculate per-game averages
    kicker_filtered = kicker_weekly[kicker_weekly['season'].isin(data_years)].copy()
    
    # Group by player/season and calculate per-game averages
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
    
    # Calculate blended projections
    blended_players = []
    for player in per_game_df['player_display_name'].unique():
        player_data = per_game_df[per_game_df['player_display_name'] == player].copy()
        player_data = player_data.sort_values('season', ascending=False)  # Most recent first
        
        if len(player_data) == 0:
            continue
            
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
