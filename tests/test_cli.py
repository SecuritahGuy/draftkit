import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from draftkit.cli import app, print_diagnostics
from draftkit.transforms.scoring import ScoringConfig


@pytest.fixture
def mock_config_file():
    """Create a temporary config file for testing."""
    config_content = """
teams: 12
roster:
  QB: 1
  RB: 2
  WR: 2
  TE: 1
  FLEX: 1
  K: 1
  DEF: 1
flex_positions: ["RB", "WR", "TE"]
scoring:
  passYdsPerPt: 25
  passTd: 4
  int: -2
  rushYdsPerPt: 10
  rushTd: 6
  rec: 1
  recYdsPerPt: 10
  recTd: 6
  twoPt: 2
  fumLost: -2
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        return Path(f.name)


@pytest.fixture
def mock_weekly_data():
    """Sample weekly data for testing."""
    return [
        {
            'season': 2024, 'week': 1, 'player_id': 'QB1', 'player_name': 'Test QB',
            'position': 'QB', 'recent_team': 'KC', 'passing_yards': 300, 'passing_tds': 3,
            'interceptions': 1, 'rushing_yards': 20, 'rushing_tds': 0, 'receptions': 0,
            'receiving_yards': 0, 'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
        },
        {
            'season': 2024, 'week': 2, 'player_id': 'QB1', 'player_name': 'Test QB',
            'position': 'QB', 'recent_team': 'KC', 'passing_yards': 250, 'passing_tds': 2,
            'interceptions': 0, 'rushing_yards': 30, 'rushing_tds': 1, 'receptions': 0,
            'receiving_yards': 0, 'receiving_tds': 0, 'fumbles_lost': 0, 'two_point_conversions': 0
        }
    ]


@pytest.fixture
def mock_roster_data():
    """Sample roster data for testing."""
    return [
        {'player_id': 'QB1', 'player_name': 'Test QB', 'position': 'QB', 'team': 'KC', 'status': 'Active'},
        {'player_id': 'RB1', 'player_name': 'Test RB', 'position': 'RB', 'team': 'SF', 'status': 'Active'}
    ]


@pytest.fixture
def mock_bye_weeks():
    """Sample bye weeks for testing."""
    return {
        'KC': 6,
        'SF': 9,
        'PHI': 5,
        'DAL': 7
    }


class TestCLI:
    """Test cases for CLI functionality."""

    def test_build_command_help(self):
        """Test that help command works."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Build players.json for the given season/year" in result.output

    @patch('draftkit.cli.load_weekly')
    @patch('draftkit.cli.load_rosters')
    @patch('draftkit.cli.load_bye_weeks')
    @patch('draftkit.cli.apply_scoring')
    @patch('draftkit.cli.compute_replacement_and_vorp')
    @patch('draftkit.cli.add_tiers_kmeans')
    def test_build_command_2024(self, mock_tiers, mock_vorp, mock_scoring, 
                               mock_bye_weeks, mock_rosters, mock_weekly, 
                               mock_config_file):
        """Test build command for 2024 (non-blended)."""
        # Setup mocks
        mock_weekly.return_value = []
        mock_rosters.return_value = []
        mock_bye_weeks.return_value = {'KC': 6}
        mock_scoring.return_value = [
            {'player_id': 'QB1', 'name': 'Test QB', 'pos': 'QB', 'tm': 'KC', 'points': 300, 'bye': 6}
        ]
        mock_vorp.return_value = [
            {'player_id': 'QB1', 'name': 'Test QB', 'pos': 'QB', 'tm': 'KC', 'points': 300, 'bye': 6, 'vorp': 50}
        ]
        mock_tiers.return_value = [
            {'player_id': 'QB1', 'name': 'Test QB', 'pos': 'QB', 'tm': 'KC', 'points': 300, 'bye': 6, 'vorp': 50, 'tier': 1}
        ]

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, [
                "--year", "2024",
                "--config", str(mock_config_file),
                "--outdir", temp_dir
            ])
            
            assert result.exit_code == 0
            assert "Loading data for 2024 (no blending)" in result.output
            assert "Bye weeks loaded for 1 teams" in result.output
            
            # Check that file was written
            output_file = Path(temp_dir) / "players.json"
            assert output_file.exists()

    @patch('draftkit.cli.load_weekly')  
    @patch('draftkit.cli.load_rosters')
    @patch('draftkit.cli.get_2025_bye_weeks')
    @patch('draftkit.cli.apply_blended_scoring')
    @patch('draftkit.cli.compute_replacement_and_vorp')
    @patch('draftkit.cli.add_tiers_kmeans')
    @patch('draftkit.cli.print_diagnostics')
    def test_build_command_2025_blended(self, mock_diagnostics, mock_tiers, mock_vorp, 
                                       mock_blended_scoring, mock_bye_weeks, 
                                       mock_rosters, mock_weekly, mock_config_file):
        """Test build command for 2025 (blended)."""
        # Setup mocks
        mock_weekly.return_value = []
        mock_rosters.return_value = []
        mock_bye_weeks.return_value = {'KC': 6}
        mock_blended_scoring.return_value = [
            {'player_id': 'QB1', 'name': 'Test QB', 'pos': 'QB', 'tm': 'KC', 'points': 300, 'bye': 6}
        ]
        mock_vorp.return_value = [
            {'player_id': 'QB1', 'name': 'Test QB', 'pos': 'QB', 'tm': 'KC', 'points': 300, 'bye': 6, 'vorp': 50}
        ]
        mock_tiers.return_value = [
            {'player_id': 'QB1', 'name': 'Test QB', 'pos': 'QB', 'tm': 'KC', 'points': 300, 'bye': 6, 'vorp': 50, 'tier': 1}
        ]

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, [
                "--year", "2025",
                "--config", str(mock_config_file),
                "--outdir", temp_dir,
                "--lookback", "3",
                "--blend", "0.6,0.3,0.1",
                "--per-game",
                "--min-games", "8"
            ])
            
            assert result.exit_code == 0
            assert "Preparing for 2025 draft using historical data from [2024, 2023, 2022]" in result.output
            assert "Blend weights: {2024: 0.6, 2023: 0.3, 2022: 0.1}" in result.output
            
            # Verify blended scoring was called with correct parameters
            mock_blended_scoring.assert_called_once()
            args, kwargs = mock_blended_scoring.call_args
            assert args[3] == [2024, 2023, 2022]  # data_years
            assert args[4] == [0.6, 0.3, 0.1]    # blend_weights
            assert args[5] == 8                   # min_games
            
            # Verify diagnostics were printed
            mock_diagnostics.assert_called_once()

    def test_build_command_blend_weight_mismatch(self, mock_config_file):
        """Test error handling when blend weights don't match lookback."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "--year", "2025",
            "--config", str(mock_config_file),
            "--lookback", "3",
            "--blend", "0.6,0.4"  # Only 2 weights for 3 lookback
        ])
        
        assert result.exit_code == 0  # Typer doesn't exit with error, just returns
        assert "Error: blend weights (2) must match lookback (3)" in result.output

    def test_print_diagnostics(self):
        """Test diagnostics printing function."""
        # Mock configuration
        cfg = Mock()
        cfg.roster = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1}
        cfg.flex_positions = ['RB', 'WR', 'TE']
        cfg.teams = 12
        
        # Mock players data
        players = [
            {'name': 'QB1', 'pos': 'QB', 'points': 300, 'vorp': 50, 'tier': 1, 'bye': 6},
            {'name': 'QB2', 'pos': 'QB', 'points': 280, 'vorp': 30, 'tier': 2, 'bye': 7},
            {'name': 'RB1', 'pos': 'RB', 'points': 250, 'vorp': 60, 'tier': 1, 'bye': 5},
            {'name': 'RB2', 'pos': 'RB', 'points': 200, 'vorp': 10, 'tier': 2, 'bye': 9},
            {'name': 'WR1', 'pos': 'WR', 'points': 180, 'vorp': 20, 'tier': 1, 'bye': 12},
            {'name': 'TE1', 'pos': 'TE', 'points': 150, 'vorp': 15, 'tier': 1, 'bye': 14}
        ]
        
        # Test that function doesn't crash (we can't easily test the rich output)
        print_diagnostics(players, cfg)

    @pytest.fixture(autouse=True)
    def cleanup_config_file(self, mock_config_file):
        """Clean up temporary config file after each test."""
        yield
        if mock_config_file.exists():
            mock_config_file.unlink()
