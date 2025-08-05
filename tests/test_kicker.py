"""Tests for kicker data loading and scoring functionality."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.draftkit.connectors.kicker import load_kicker_weekly, load_kicker_rosters
from src.draftkit.transforms.scoring import ScoringConfig, _score_kicker_row, apply_kicker_scoring, apply_kicker_blended_scoring


class TestKickerDataLoading:
    """Test kicker data loading from play-by-play data."""

    @patch('src.draftkit.connectors.kicker.nfl')
    def test_load_kicker_weekly_success(self, mock_nfl):
        """Test successful kicker weekly data loading."""
        # Mock PBP data with kicking plays
        mock_pbp = pd.DataFrame([
            {
                'season': 2023, 'week': 1, 'play_type': 'field_goal',
                'kicker_player_name': 'J.Tucker', 'kicker_player_id': '00-0026858', 'posteam': 'BAL',
                'kick_distance': 45, 'field_goal_result': 'made'
            },
            {
                'season': 2023, 'week': 1, 'play_type': 'field_goal',
                'kicker_player_name': 'J.Tucker', 'kicker_player_id': '00-0026858', 'posteam': 'BAL',
                'kick_distance': 55, 'field_goal_result': 'made'
            },
            {
                'season': 2023, 'week': 1, 'play_type': 'extra_point',
                'kicker_player_name': 'J.Tucker', 'kicker_player_id': '00-0026858', 'posteam': 'BAL',
                'extra_point_result': 'good'
            }
        ])
        mock_nfl.import_pbp_data.return_value = mock_pbp
        
        result = load_kicker_weekly([2023])
        
        assert len(result) == 1
        assert result.iloc[0]['player_display_name'] == 'J.Tucker'
        assert result.iloc[0]['team'] == 'BAL'
        assert result.iloc[0]['fg_40_49'] == 1  # 45-yard FG
        assert result.iloc[0]['fg_50_plus'] == 1  # 55-yard FG
        assert result.iloc[0]['xp_made'] == 1

    @patch('src.draftkit.connectors.kicker.nfl')
    def test_load_kicker_rosters_success(self, mock_nfl):
        """Test successful kicker roster loading."""
        mock_rosters = pd.DataFrame([
            {'player_display_name': 'J.Tucker', 'team': 'BAL', 'position': 'K'},
            {'player_display_name': 'H.Butker', 'team': 'KC', 'position': 'K'}
        ])
        mock_nfl.import_rosters.return_value = mock_rosters
        
        result = load_kicker_rosters(2023)
        
        assert len(result) == 2
        assert 'J.Tucker' in result['player_display_name'].values
        assert 'H.Butker' in result['player_display_name'].values

    def test_load_kicker_weekly_empty_years(self):
        """Test loading kicker data with empty years list."""
        result = load_kicker_weekly([])
        assert len(result) == 0


class TestKickerScoring:
    """Test kicker fantasy scoring calculations."""

    def test_score_kicker_row_basic(self):
        """Test basic kicker scoring calculation."""
        cfg = ScoringConfig(
            k_fg_0_39=3, k_fg_40_49=4, k_fg_50_plus=5, k_xp=1
        )
        
        row = {
            'fg_0_39': 2,      # 2 * 3 = 6 points
            'fg_40_49': 1,     # 1 * 4 = 4 points  
            'fg_50_plus': 1,   # 1 * 5 = 5 points
            'xp_made': 3       # 3 * 1 = 3 points
        }
        
        points = _score_kicker_row(row, cfg)
        assert points == 18.0  # 6 + 4 + 5 + 3

    def test_score_kicker_row_with_misses(self):
        """Test kicker scoring with miss penalties."""
        cfg = ScoringConfig(
            k_fg_0_39=3, k_xp=1, k_fg_miss=-1, k_xp_miss=-0.5
        )
        
        row = {
            'fg_0_39': 2,      # 2 * 3 = 6 points
            'xp_made': 1,      # 1 * 1 = 1 point
            'fg_miss': 1,      # 1 * -1 = -1 point
            'xp_miss': 2       # 2 * -0.5 = -1 point
        }
        
        points = _score_kicker_row(row, cfg)
        assert points == 5.0  # 6 + 1 - 1 - 1

    def test_apply_kicker_scoring_basic(self):
        """Test applying kicker scoring to weekly data."""
        cfg = ScoringConfig(k_fg_0_39=3, k_xp=1)
        
        weekly = pd.DataFrame([
            {
                'season': 2023, 'week': 1, 'player_display_name': 'J.Tucker',
                'team': 'BAL', 'fg_0_39': 1, 'xp_made': 2
            }
        ])
        
        rosters = pd.DataFrame([
            {'player_display_name': 'J.Tucker', 'team': 'BAL', 'position': 'K'}
        ])
        
        result = apply_kicker_scoring(weekly, rosters, cfg)
        
        assert len(result) == 1
        assert result[0]['name'] == 'J.Tucker'
        assert result[0]['pos'] == 'K'
        assert result[0]['tm'] == 'BAL'
        assert result[0]['points'] == 5.0  # 1*3 + 2*1

    def test_apply_kicker_scoring_with_bye_weeks(self):
        """Test kicker scoring with bye week information."""
        cfg = ScoringConfig(k_fg_0_39=3)
        
        weekly = pd.DataFrame([
            {
                'season': 2023, 'week': 1, 'player_display_name': 'J.Tucker',
                'team': 'BAL', 'fg_0_39': 1
            }
        ])
        
        rosters = pd.DataFrame([
            {'player_display_name': 'J.Tucker', 'team': 'BAL', 'position': 'K'}
        ])
        
        result = apply_kicker_scoring(weekly, rosters, cfg, bye_weeks={'BAL': 14})
        
        assert len(result) == 1
        assert result[0]['bye'] == 14

    def test_apply_kicker_blended_scoring_basic(self):
        """Test blended kicker scoring across multiple seasons."""
        cfg = ScoringConfig(k_fg_0_39=3, k_xp=1)
        
        # Multi-season data for same kicker
        weekly = pd.DataFrame([
            {
                'season': 2023, 'week': 1, 'player_display_name': 'J.Tucker',
                'team': 'BAL', 'fg_0_39': 2, 'xp_made': 3
            },
            {
                'season': 2022, 'week': 1, 'player_display_name': 'J.Tucker',
                'team': 'BAL', 'fg_0_39': 1, 'xp_made': 2
            }
        ])
        
        rosters = pd.DataFrame([
            {'player_display_name': 'J.Tucker', 'team': 'BAL', 'position': 'K'}
        ])
        
        result = apply_kicker_blended_scoring(
            weekly, rosters, cfg,
            data_years=[2023, 2022], blend_weights=[0.6, 0.4], min_games=1
        )
        
        assert len(result) == 1
        assert result[0]['name'] == 'J.Tucker'
        # Should project blended per-game stats to full 17-game season
        assert result[0]['points'] > 0
