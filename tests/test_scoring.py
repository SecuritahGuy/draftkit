import pytest
import pandas as pd
import tempfile
from pathlib import Path

from draftkit.transforms.scoring import (
    ScoringConfig, _score_row, apply_scoring, apply_blended_scoring
)


class TestScoringConfig:
    """Test cases for ScoringConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        cfg = ScoringConfig()
        assert cfg.pass_yds_per_pt == 25.0
        assert cfg.pass_td == 4.0
        assert cfg.interceptions == -2.0
        assert cfg.rush_yds_per_pt == 10.0
        assert cfg.rush_td == 6.0
        assert cfg.rec == 1.0
        assert cfg.rec_yds_per_pt == 10.0
        assert cfg.rec_td == 6.0
        assert cfg.two_pt == 2.0
        assert cfg.fum_lost == -2.0
        assert cfg.teams == 12

    def test_from_yaml(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
teams: 10
roster:
  QB: 1
  RB: 2
  WR: 3
  TE: 1
  FLEX: 1
  K: 1  
  DEF: 1
flex_positions: ["RB", "WR", "TE"]
scoring:
  passYdsPerPt: 20
  passTd: 6
  int: -1
  rushYdsPerPt: 15
  rushTd: 4
  rec: 0.5
  recYdsPerPt: 20
  recTd: 4
  twoPt: 3
  fumLost: -1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            config_path = Path(f.name)

        try:
            cfg = ScoringConfig.from_yaml(config_path)
            assert cfg.teams == 10
            assert cfg.roster['QB'] == 1
            assert cfg.roster['WR'] == 3
            assert cfg.flex_positions == ['RB', 'WR', 'TE']
            assert cfg.pass_yds_per_pt == 20
            assert cfg.pass_td == 6
            assert cfg.interceptions == -1
            assert cfg.rush_yds_per_pt == 15
            assert cfg.rush_td == 4
            assert cfg.rec == 0.5
            assert cfg.rec_yds_per_pt == 20
            assert cfg.rec_td == 4
            assert cfg.two_pt == 3
            assert cfg.fum_lost == -1
        finally:
            config_path.unlink()


class TestScoreRow:
    """Test cases for _score_row function."""

    def test_basic_scoring(self):
        """Test basic scoring calculation."""
        cfg = ScoringConfig()
        row = {
            'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
            'rushing_yards': 20, 'rushing_tds': 0,
            'receptions': 5, 'receiving_yards': 60, 'receiving_tds': 1,
            'two_point_conversions': 0, 'fumbles_lost': 0
        }
        pts = _score_row(row, cfg)
        # 250/25=10 + 2*4=8 -1*2=-2 + 20/10=2 + 5*1=5 + 60/10=6 + 1*6=6 = 35
        assert pts == 35.0

    def test_qb_scoring(self):
        """Test QB-specific scoring."""
        cfg = ScoringConfig()
        row = {
            'passing_yards': 300, 'passing_tds': 3, 'interceptions': 1,
            'rushing_yards': 50, 'rushing_tds': 1,
            'receptions': 0, 'receiving_yards': 0, 'receiving_tds': 0,
            'two_point_conversions': 1, 'fumbles_lost': 1
        }
        pts = _score_row(row, cfg)
        # 300/25=12 + 3*4=12 -1*2=-2 + 50/10=5 + 1*6=6 + 1*2=2 -1*2=-2 = 33
        assert pts == 33.0

    def test_rb_scoring(self):
        """Test RB-specific scoring."""
        cfg = ScoringConfig()
        row = {
            'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
            'rushing_yards': 120, 'rushing_tds': 2,
            'receptions': 4, 'receiving_yards': 30, 'receiving_tds': 0,
            'two_point_conversions': 0, 'fumbles_lost': 1
        }
        pts = _score_row(row, cfg)
        # 120/10=12 + 2*6=12 + 4*1=4 + 30/10=3 -1*2=-2 = 29
        assert pts == 29.0

    def test_wr_scoring(self):
        """Test WR-specific scoring."""
        cfg = ScoringConfig()
        row = {
            'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
            'rushing_yards': 10, 'rushing_tds': 0,
            'receptions': 8, 'receiving_yards': 100, 'receiving_tds': 1,
            'two_point_conversions': 0, 'fumbles_lost': 0
        }
        pts = _score_row(row, cfg)
        # 10/10=1 + 8*1=8 + 100/10=10 + 1*6=6 = 25
        assert pts == 25.0

    def test_missing_stats(self):
        """Test handling of missing statistics."""
        cfg = ScoringConfig()
        row = {
            'passing_yards': 200,  # Only one stat present
        }
        pts = _score_row(row, cfg)
        # 200/25=8, everything else defaults to 0
        assert pts == 8.0


class TestApplyScoring:
    """Test cases for apply_scoring function."""

    def test_apply_scoring_basic(self):
        """Test basic apply_scoring functionality."""
        # Create sample data
        weekly_data = pd.DataFrame([
            {
                'player_id': 'QB1', 'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
                'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            },
            {
                'player_id': 'QB1', 'passing_yards': 300, 'passing_tds': 3, 'interceptions': 0,
                'rushing_yards': 30, 'rushing_tds': 1, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 1, 'two_point_conversions': 0
            }
        ])
        
        roster_data = pd.DataFrame([
            {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC'}
        ])
        
        cfg = ScoringConfig()
        players = apply_scoring(weekly_data, roster_data, cfg)
        
        assert len(players) == 1
        player = players[0]
        assert player['player_id'] == 'QB1'
        assert player['name'] == 'Test QB'
        assert player['pos'] == 'QB'
        assert player['tm'] == 'KC'
        # Total: (250+300)/25 + (2+3)*4 + (1)*-2 + (20+30)/10 + (0+1)*6 + (0+1)*-2
        #      = 22 + 20 - 2 + 5 + 6 - 2 = 49
        assert player['points'] == 49.0

    def test_apply_scoring_with_bye_weeks(self):
        """Test apply_scoring with bye weeks."""
        weekly_data = pd.DataFrame([
            {
                'player_id': 'QB1', 'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
                'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            }
        ])
        
        roster_data = pd.DataFrame([
            {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC'}
        ])
        
        bye_weeks = {'KC': 6, 'SF': 9}
        cfg = ScoringConfig()
        players = apply_scoring(weekly_data, roster_data, cfg, bye_weeks)
        
        assert len(players) == 1
        player = players[0]
        assert player['bye'] == 6

    def test_apply_scoring_filters_positions(self):
        """Test that apply_scoring only includes offense positions."""
        weekly_data = pd.DataFrame([
            {
                'player_id': 'QB1', 'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
                'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            }
        ])
        
        roster_data = pd.DataFrame([
            {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC'},
            {'player_id': 'K1', 'player_name': 'Test K', 'position': 'K', 'team': 'KC'},
            {'player_id': 'DEF1', 'player_name': 'Test DEF', 'position': 'DEF', 'team': 'KC'}
        ])
        
        cfg = ScoringConfig()
        players = apply_scoring(weekly_data, roster_data, cfg)
        
        # Should only include QB (offense position)
        assert len(players) == 1
        assert players[0]['pos'] == 'QB'


class TestApplyBlendedScoring:
    """Test cases for apply_blended_scoring function."""

    def test_apply_blended_scoring_basic(self):
        """Test basic blended scoring functionality."""
        # Create sample data with multiple seasons
        weekly_data = pd.DataFrame([
            # 2024 data - QB1 plays 10 games, averages good performance
            *[{
                'season': 2024, 'week': i, 'player_id': 'QB1',
                'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
                'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            } for i in range(1, 11)],
            # 2023 data - QB1 plays 12 games, slightly different performance
            *[{
                'season': 2023, 'week': i, 'player_id': 'QB1',
                'passing_yards': 280, 'passing_tds': 2, 'interceptions': 0,
                'rushing_yards': 30, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            } for i in range(1, 13)]
        ])
        
        roster_data = pd.DataFrame([
            {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC'}
        ])
        
        cfg = ScoringConfig()
        data_years = [2024, 2023]
        blend_weights = [0.7, 0.3]
        min_games = 8
        
        players = apply_blended_scoring(weekly_data, roster_data, cfg, data_years, blend_weights, min_games)
        
        assert len(players) == 1
        player = players[0]
        assert player['player_id'] == 'QB1'
        assert player['name'] == 'Test QB'
        assert player['pos'] == 'QB'
        assert player['tm'] == 'KC'
        assert 'points' in player
        assert player['points'] > 0

    def test_apply_blended_scoring_min_games_filter(self):
        """Test that min_games filter works correctly."""
        # Create sample data where QB1 doesn't meet min_games in one season
        weekly_data = pd.DataFrame([
            # 2024 data - QB1 plays only 5 games (below min_games=8)
            *[{
                'season': 2024, 'week': i, 'player_id': 'QB1',
                'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
                'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            } for i in range(1, 6)],
            # 2023 data - QB1 plays 12 games (meets min_games=8)
            *[{
                'season': 2023, 'week': i, 'player_id': 'QB1',
                'passing_yards': 280, 'passing_tds': 2, 'interceptions': 0,
                'rushing_yards': 30, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            } for i in range(1, 13)]
        ])
        
        roster_data = pd.DataFrame([
            {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC'}
        ])
        
        cfg = ScoringConfig()
        data_years = [2024, 2023]
        blend_weights = [0.7, 0.3]
        min_games = 8
        
        players = apply_blended_scoring(weekly_data, roster_data, cfg, data_years, blend_weights, min_games)
        
        # Should still include QB1 since they met min_games in 2023
        assert len(players) == 1
        player = players[0]
        assert player['player_id'] == 'QB1'

    def test_apply_blended_scoring_with_bye_weeks(self):
        """Test blended scoring with bye weeks."""
        weekly_data = pd.DataFrame([
            {
                'season': 2024, 'week': 1, 'player_id': 'QB1',
                'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
                'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0, 'receiving_yards': 0,
                'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            } for _ in range(10)  # 10 games to meet min_games
        ])
        
        roster_data = pd.DataFrame([
            {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC'}
        ])
        
        bye_weeks = {'KC': 6}
        cfg = ScoringConfig()
        data_years = [2024]
        blend_weights = [1.0]
        min_games = 8
        
        players = apply_blended_scoring(weekly_data, roster_data, cfg, data_years, blend_weights, min_games, bye_weeks)
        
        assert len(players) == 1
        player = players[0]
        assert player['bye'] == 6
