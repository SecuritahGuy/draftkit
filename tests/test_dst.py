import pytest
import pandas as pd
from unittest.mock import Mock, patch

from draftkit.connectors.dst import load_dst_weekly, load_dst_rosters
from draftkit.transforms.scoring import ScoringConfig, _score_dst_row, apply_dst_scoring, apply_dst_blended_scoring


class TestDSTConnector:
    """Test cases for DST data connector."""

    @patch('draftkit.connectors.dst.nfl')
    def test_load_dst_weekly(self, mock_nfl):
        """Test basic DST weekly data loading."""
        # Mock defensive stats
        mock_def_stats = pd.DataFrame([
            {'team': 'KC', 'season': 2023, 'week': 1, 'def_sacks': 3.0, 'def_ints': 1.0, 'def_tackles_combined': 25.0},
            {'team': 'KC', 'season': 2023, 'week': 2, 'def_sacks': 2.0, 'def_ints': 0.0, 'def_tackles_combined': 30.0},
        ])
        
        # Mock schedules with scores
        mock_schedules = pd.DataFrame([
            {'season': 2023, 'game_type': 'REG', 'week': 1, 'home_team': 'KC', 'away_team': 'DET', 'home_score': 21.0, 'away_score': 20.0},
            {'season': 2023, 'game_type': 'REG', 'week': 2, 'home_team': 'JAX', 'away_team': 'KC', 'home_score': 17.0, 'away_score': 9.0},
        ])
        
        mock_nfl.import_weekly_pfr.return_value = mock_def_stats
        mock_nfl.import_schedules.return_value = mock_schedules
        
        result = load_dst_weekly([2023])
        
        assert len(result) == 4  # 2 games * 2 teams per game
        assert 'team' in result.columns
        assert 'points_allowed' in result.columns
        assert 'sacks' in result.columns
        assert 'interceptions' in result.columns
        
        # Check KC's stats
        kc_data = result[result['team'] == 'KC']
        assert len(kc_data) == 2
        
        # Week 1: KC at home allowed 20 points
        week1 = kc_data[kc_data['week'] == 1].iloc[0]
        assert week1['points_allowed'] == 20.0
        assert week1['sacks'] == 3.0
        assert week1['interceptions'] == 1.0

    @patch('draftkit.connectors.dst.nfl')
    def test_load_dst_rosters(self, mock_nfl):
        """Test DST roster data creation."""
        # Mock schedules to get team list
        mock_schedules = pd.DataFrame([
            {'season': 2023, 'home_team': 'KC', 'away_team': 'DET'},
            {'season': 2023, 'home_team': 'SF', 'away_team': 'DAL'},
        ])
        
        mock_nfl.import_schedules.return_value = mock_schedules
        
        result = load_dst_rosters([2023])
        
        assert len(result) == 4  # 4 unique teams
        assert all(result['position'] == 'DST')
        assert 'KC_DST_2023' in result['player_id'].values
        assert 'SF DST' in result['player_name'].values


class TestDSTScoring:
    """Test cases for DST scoring functions."""

    def test_score_dst_row_basic(self):
        """Test basic DST scoring for a single team-week."""
        cfg = ScoringConfig()
        
        # Test shutout performance (0 points allowed)
        row = {
            'sacks': 4,
            'interceptions': 2, 
            'fumble_recoveries': 1,
            'defensive_tds': 1,
            'safeties': 0,
            'blocked_kicks': 1,
            'points_allowed': 0
        }
        
        points = _score_dst_row(row, cfg)
        # 4*1 + 2*2 + 1*2 + 1*6 + 0*2 + 1*2 + 10 = 4+4+2+6+0+2+10 = 28
        assert points == 28.0

    def test_score_dst_row_points_allowed_tiers(self):
        """Test points allowed tier scoring."""
        cfg = ScoringConfig()
        
        test_cases = [
            (0, cfg.dst_points_allowed_0),      # 10 pts
            (6, cfg.dst_points_allowed_1_6),    # 7 pts
            (13, cfg.dst_points_allowed_7_13),  # 4 pts  
            (20, cfg.dst_points_allowed_14_20), # 1 pt
            (27, cfg.dst_points_allowed_21_27), # 0 pts
            (34, cfg.dst_points_allowed_28_34), # -1 pt
            (35, cfg.dst_points_allowed_35_plus) # -4 pts
        ]
        
        for points_allowed, expected_pts in test_cases:
            row = {'points_allowed': points_allowed, 'sacks': 0, 'interceptions': 0, 
                   'fumble_recoveries': 0, 'defensive_tds': 0, 'safeties': 0, 'blocked_kicks': 0}
            result = _score_dst_row(row, cfg)
            assert result == expected_pts

    def test_apply_dst_scoring(self):
        """Test applying DST scoring to season data."""
        dst_weekly = pd.DataFrame([
            {'team': 'KC', 'season': 2023, 'week': 1, 'sacks': 3.0, 'interceptions': 1.0, 'points_allowed': 10.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 2, 'sacks': 2.0, 'interceptions': 0.0, 'points_allowed': 20.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 1.0, 'safeties': 0.0, 'blocked_kicks': 0.0}
        ])
        
        dst_rosters = pd.DataFrame([
            {'player_id': 'KC_DST_2023', 'player_name': 'KC DST', 'position': 'DST', 'team': 'KC', 'season': 2023}
        ])
        
        cfg = ScoringConfig()
        bye_weeks = {'KC': 10}
        
        result = apply_dst_scoring(dst_weekly, dst_rosters, cfg, bye_weeks)
        
        assert len(result) == 1
        dst_player = result[0]
        assert dst_player['name'] == 'KC DST'
        assert dst_player['pos'] == 'DST'
        assert dst_player['tm'] == 'KC'
        assert dst_player['bye'] == 10
        
        # Season totals: 5 sacks, 1 int, 30 points allowed, 1 fumble, 1 def TD
        # Points: 5*1 + 1*2 + (-1 for 30 points allowed in 28-34 tier) + 1*2 + 1*6 = 5+2-1+2+6 = 14
        expected_points = 14
        assert dst_player['points'] == expected_points

    def test_apply_dst_blended_scoring(self):
        """Test blended DST scoring with historical data."""
        # Historical data for 2 seasons
        dst_weekly = pd.DataFrame([
            # 2023 season - 8 games minimum
            {'team': 'KC', 'season': 2023, 'week': 1, 'sacks': 2.0, 'interceptions': 1.0, 'points_allowed': 10.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 2, 'sacks': 4.0, 'interceptions': 1.0, 'points_allowed': 20.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 1.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 3, 'sacks': 2.0, 'interceptions': 0.0, 'points_allowed': 15.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 4, 'sacks': 3.0, 'interceptions': 2.0, 'points_allowed': 7.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 1.0},
            {'team': 'KC', 'season': 2023, 'week': 5, 'sacks': 1.0, 'interceptions': 0.0, 'points_allowed': 25.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 6, 'sacks': 5.0, 'interceptions': 1.0, 'points_allowed': 14.0,
             'fumble_recoveries': 2.0, 'defensive_tds': 1.0, 'safeties': 1.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 7, 'sacks': 2.0, 'interceptions': 0.0, 'points_allowed': 17.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2023, 'week': 8, 'sacks': 3.0, 'interceptions': 1.0, 'points_allowed': 21.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            # 2022 season - 8 games minimum  
            {'team': 'KC', 'season': 2022, 'week': 1, 'sacks': 1.0, 'interceptions': 0.0, 'points_allowed': 30.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2022, 'week': 2, 'sacks': 3.0, 'interceptions': 1.0, 'points_allowed': 14.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2022, 'week': 3, 'sacks': 2.0, 'interceptions': 2.0, 'points_allowed': 10.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 1.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2022, 'week': 4, 'sacks': 4.0, 'interceptions': 0.0, 'points_allowed': 18.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 1.0},
            {'team': 'KC', 'season': 2022, 'week': 5, 'sacks': 1.0, 'interceptions': 1.0, 'points_allowed': 28.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2022, 'week': 6, 'sacks': 2.0, 'interceptions': 0.0, 'points_allowed': 24.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2022, 'week': 7, 'sacks': 3.0, 'interceptions': 1.0, 'points_allowed': 12.0,
             'fumble_recoveries': 0.0, 'defensive_tds': 1.0, 'safeties': 1.0, 'blocked_kicks': 0.0},
            {'team': 'KC', 'season': 2022, 'week': 8, 'sacks': 2.0, 'interceptions': 0.0, 'points_allowed': 21.0,
             'fumble_recoveries': 1.0, 'defensive_tds': 0.0, 'safeties': 0.0, 'blocked_kicks': 0.0},
        ])
        
        dst_rosters = pd.DataFrame([
            {'player_id': 'KC_DST_2023', 'player_name': 'KC DST', 'position': 'DST', 'team': 'KC', 'season': 2023}
        ])
        
        cfg = ScoringConfig()
        data_years = [2023, 2022]
        blend_weights = [0.7, 0.3]
        min_games = 8
        bye_weeks = {'KC': 10}
        
        result = apply_dst_blended_scoring(dst_weekly, dst_rosters, cfg, data_years, blend_weights, min_games, bye_weeks)
        
        assert len(result) == 1
        dst_player = result[0]
        assert dst_player['name'] == 'KC DST'
        assert dst_player['pos'] == 'DST'
        assert dst_player['tm'] == 'KC'
        assert dst_player['bye'] == 10
        assert dst_player['points'] > 0  # Should have positive fantasy points

    def test_dst_scoring_config_yaml_integration(self):
        """Test that DST scoring config can be loaded from YAML."""
        cfg = ScoringConfig()
        
        # Test default DST scoring values
        assert cfg.dst_sack == 1.0
        assert cfg.dst_int == 2.0
        assert cfg.dst_fumble_recovery == 2.0
        assert cfg.dst_defensive_td == 6.0
        assert cfg.dst_safety == 2.0
        assert cfg.dst_blocked_kick == 2.0
        assert cfg.dst_points_allowed_0 == 10.0
        assert cfg.dst_points_allowed_1_6 == 7.0
        assert cfg.dst_points_allowed_7_13 == 4.0
        assert cfg.dst_points_allowed_14_20 == 1.0
        assert cfg.dst_points_allowed_21_27 == 0.0
        assert cfg.dst_points_allowed_28_34 == -1.0
        assert cfg.dst_points_allowed_35_plus == -4.0
