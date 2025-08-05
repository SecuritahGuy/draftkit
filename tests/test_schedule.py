import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from draftkit.connectors.schedule import load_bye_weeks, get_2025_bye_weeks


class TestScheduleConnector:
    """Test cases for schedule connector functions."""

    @patch('draftkit.connectors.schedule.nfl')
    def test_load_bye_weeks(self, mock_nfl):
        """Test loading bye weeks from schedule data."""
        # Mock schedule data
        mock_schedule_data = pd.DataFrame([
            # Week 1 - all teams play except ARI, BUF
            {'season': 2024, 'game_type': 'REG', 'week': 1, 'home_team': 'KC', 'away_team': 'BAL'},
            {'season': 2024, 'game_type': 'REG', 'week': 1, 'home_team': 'PHI', 'away_team': 'GB'},
            # Week 2 - all teams play except KC, BAL (on bye)
            {'season': 2024, 'game_type': 'REG', 'week': 2, 'home_team': 'ARI', 'away_team': 'BUF'},
            {'season': 2024, 'game_type': 'REG', 'week': 2, 'home_team': 'PHI', 'away_team': 'GB'},
            # Include some playoff games to test filtering
            {'season': 2024, 'game_type': 'WC', 'week': 19, 'home_team': 'KC', 'away_team': 'BAL'},
        ])
        
        mock_nfl.import_schedules.return_value = mock_schedule_data
        
        bye_weeks = load_bye_weeks(2024)
        
        # ARI and BUF should have bye week 1, KC and BAL should have bye week 2
        expected_byes = {'ARI': 1, 'BUF': 1, 'KC': 2, 'BAL': 2}
        assert bye_weeks == expected_byes
        
        # Verify import_schedules was called with correct year
        mock_nfl.import_schedules.assert_called_once_with([2024])

    @patch('draftkit.connectors.schedule.load_bye_weeks')
    def test_get_2025_bye_weeks(self, mock_load_bye_weeks):
        """Test getting 2025 bye weeks (should use 2024 data)."""
        mock_bye_weeks = {'KC': 6, 'SF': 9, 'PHI': 5}
        mock_load_bye_weeks.return_value = mock_bye_weeks
        
        result = get_2025_bye_weeks()
        
        assert result == mock_bye_weeks
        mock_load_bye_weeks.assert_called_once_with(2024)

    @patch('draftkit.connectors.schedule.nfl')
    def test_load_bye_weeks_empty_data(self, mock_nfl):
        """Test handling of empty schedule data."""
        # Empty dataframe with correct columns structure
        empty_df = pd.DataFrame(columns=['season', 'game_type', 'week', 'home_team', 'away_team'])
        mock_nfl.import_schedules.return_value = empty_df
        
        bye_weeks = load_bye_weeks(2024)
        
        assert bye_weeks == {}

    @patch('draftkit.connectors.schedule.nfl')  
    def test_load_bye_weeks_no_byes(self, mock_nfl):
        """Test when no teams have bye weeks (all teams play every week)."""
        # Mock data where same teams play every week (unrealistic but tests edge case)
        mock_schedule_data = pd.DataFrame([
            {'season': 2024, 'game_type': 'REG', 'week': 1, 'home_team': 'KC', 'away_team': 'BAL'},
            {'season': 2024, 'game_type': 'REG', 'week': 2, 'home_team': 'KC', 'away_team': 'BAL'},
        ])
        
        mock_nfl.import_schedules.return_value = mock_schedule_data
        
        bye_weeks = load_bye_weeks(2024)
        
        # Should be empty since no teams have byes
        assert bye_weeks == {}
