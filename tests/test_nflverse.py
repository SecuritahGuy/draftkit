import pytest
import pandas as pd
from unittest.mock import Mock, patch

from draftkit.connectors.nflverse import load_weekly, load_rosters


class TestNFLVerseConnector:
    """Test cases for nflverse connector functions."""

    @patch('draftkit.connectors.nflverse.nfl')
    def test_load_weekly(self, mock_nfl):
        """Test loading weekly data."""
        # Mock weekly data from nfl_data_py
        mock_weekly_data = pd.DataFrame([
            {
                'season': 2024, 'week': 1, 'player_id': 'QB1', 'player_name': 'Test QB',
                'position': 'QB', 'recent_team': 'KC', 'passing_yards': 250, 'passing_tds': 2,
                'interceptions': 1, 'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0,
                'receiving_yards': 0, 'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0,
                'extra_column': 'should_be_filtered'
            },
            {
                'season': 2024, 'week': 2, 'player_id': 'RB1', 'player_name': 'Test RB',
                'position': 'RB', 'recent_team': 'SF', 'passing_yards': 0, 'passing_tds': 0,
                'interceptions': 0, 'rushing_yards': 120, 'rushing_tds': 1, 'receptions': 3,
                'receiving_yards': 25, 'receiving_tds': 0, 'fumbles_lost': 1, 'two_point_conversions': 0
            }
        ])
        
        mock_nfl.import_weekly_data.return_value = mock_weekly_data
        
        result = load_weekly([2024])
        
        # Verify the function was called correctly
        mock_nfl.import_weekly_data.assert_called_once_with([2024])
        
        # Check that result has expected structure
        assert len(result) == 2
        
        # Check that only needed columns are returned
        expected_columns = [
            'season', 'week', 'player_id', 'player_name', 'position', 'recent_team',
            'passing_yards', 'passing_tds', 'interceptions',
            'rushing_yards', 'rushing_tds',
            'receptions', 'receiving_yards', 'receiving_tds',
            'fumbles_lost', 'two_point_conversions'
        ]
        
        for col in expected_columns:
            assert col in result.columns
            
        # Extra column should be filtered out
        assert 'extra_column' not in result.columns
        
        # Check specific values
        qb_row = result[result['player_id'] == 'QB1'].iloc[0]
        assert qb_row['passing_yards'] == 250
        assert qb_row['passing_tds'] == 2
        
        rb_row = result[result['player_id'] == 'RB1'].iloc[0]
        assert rb_row['rushing_yards'] == 120
        assert rb_row['rushing_tds'] == 1

    @patch('draftkit.connectors.nflverse.nfl')
    def test_load_weekly_missing_columns(self, mock_nfl):
        """Test load_weekly when some columns are missing from the data."""
        # Mock data missing some columns
        mock_weekly_data = pd.DataFrame([
            {
                'season': 2024, 'week': 1, 'player_id': 'QB1', 'player_name': 'Test QB',
                'position': 'QB', 'recent_team': 'KC', 'passing_yards': 250, 'passing_tds': 2,
                'interceptions': 1, 'rushing_yards': 20, 'rushing_tds': 0
                # Missing receiving stats, fumbles, two_point_conversions
            }
        ])
        
        mock_nfl.import_weekly_data.return_value = mock_weekly_data
        
        result = load_weekly([2024])
        
        # Missing columns should be filled with 0
        assert result.iloc[0]['receptions'] == 0
        assert result.iloc[0]['receiving_yards'] == 0
        assert result.iloc[0]['receiving_tds'] == 0
        assert result.iloc[0]['fumbles_lost'] == 0
        assert result.iloc[0]['two_point_conversions'] == 0

    @patch('draftkit.connectors.nflverse.nfl')
    def test_load_weekly_multiple_years(self, mock_nfl):
        """Test loading weekly data for multiple years."""
        mock_weekly_data = pd.DataFrame([
            {
                'season': 2024, 'week': 1, 'player_id': 'QB1', 'player_name': 'Test QB',
                'position': 'QB', 'recent_team': 'KC', 'passing_yards': 250, 'passing_tds': 2,
                'interceptions': 1, 'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0,
                'receiving_yards': 0, 'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            },
            {
                'season': 2023, 'week': 1, 'player_id': 'QB1', 'player_name': 'Test QB',
                'position': 'QB', 'recent_team': 'KC', 'passing_yards': 280, 'passing_tds': 3,
                'interceptions': 0, 'rushing_yards': 30, 'rushing_tds': 1, 'receptions': 0,
                'receiving_yards': 0, 'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
            }
        ])
        
        mock_nfl.import_weekly_data.return_value = mock_weekly_data
        
        result = load_weekly([2024, 2023])
        
        mock_nfl.import_weekly_data.assert_called_once_with([2024, 2023])
        assert len(result) == 2
        assert 2024 in result['season'].values
        assert 2023 in result['season'].values

    @patch('draftkit.connectors.nflverse.nfl')
    def test_load_rosters(self, mock_nfl):
        """Test loading roster data."""
        # Mock roster data from nfl_data_py
        mock_roster_data = pd.DataFrame([
            {
                'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB',
                'team': 'KC', 'status': 'Active', 'extra_column': 'should_be_filtered'
            },
            {
                'player_id': 'RB1', 'player_name': 'Test RB', 'position': 'RB',
                'team': 'SF', 'status': 'Active'
            },
            # Duplicate entry - should be removed
            {
                'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB',
                'team': 'KC', 'status': 'Active'
            }
        ])
        
        mock_nfl.import_seasonal_rosters.return_value = mock_roster_data
        
        result = load_rosters([2024])
        
        # Verify the function was called correctly
        mock_nfl.import_seasonal_rosters.assert_called_once_with([2024])
        
        # Check that duplicates are removed
        assert len(result) == 2
        
        # Check that only needed columns are returned
        expected_columns = ['player_id', 'player_name', 'position', 'team', 'status']
        for col in expected_columns:
            assert col in result.columns
            
        # Extra column should be filtered out
        assert 'extra_column' not in result.columns
        
        # Check specific values
        qb_row = result[result['player_id'] == 'QB1'].iloc[0]
        assert qb_row['player_name'] == 'Test QB'
        assert qb_row['position'] == 'QB'
        assert qb_row['team'] == 'KC'
        assert qb_row['status'] == 'Active'

    @patch('draftkit.connectors.nflverse.nfl')
    def test_load_rosters_missing_columns(self, mock_nfl):
        """Test load_rosters when some columns are missing."""
        # Mock data missing some columns
        mock_roster_data = pd.DataFrame([
            {
                'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB'
                # Missing team and status
            }
        ])
        
        mock_nfl.import_seasonal_rosters.return_value = mock_roster_data
        
        result = load_rosters([2024])
        
        # Missing columns should be filled with None
        assert result.iloc[0]['team'] is None
        assert result.iloc[0]['status'] is None

    @patch('draftkit.connectors.nflverse.nfl')
    def test_load_rosters_multiple_years(self, mock_nfl):
        """Test loading roster data for multiple years."""
        mock_roster_data = pd.DataFrame([
            {
                'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB',
                'team': 'KC', 'status': 'Active'
            },
            {
                'player_id': 'QB2', 'player_name': 'Test QB2', 'position': 'QB',
                'team': 'SF', 'status': 'Active'
            }
        ])
        
        mock_nfl.import_seasonal_rosters.return_value = mock_roster_data
        
        result = load_rosters([2024, 2023])
        
        mock_nfl.import_seasonal_rosters.assert_called_once_with([2024, 2023])
        assert len(result) == 2
