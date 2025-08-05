import pytest
import numpy as np
from unittest.mock import Mock, patch

from draftkit.transforms.tiers import compute_replacement_and_vorp, add_tiers_kmeans
from draftkit.transforms.scoring import ScoringConfig


class TestTiers:
    """Test cases for tier-related functions."""

    def test_compute_replacement_and_vorp(self):
        """Test replacement level and VORP calculation."""
        # Mock configuration
        cfg = ScoringConfig()
        cfg.teams = 12
        cfg.roster = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1}
        cfg.flex_positions = ['RB', 'WR', 'TE']
        
        # Sample players data
        players = [
            {'player_id': 'QB1', 'name': 'Elite QB', 'pos': 'QB', 'tm': 'KC', 'points': 400},
            {'player_id': 'QB2', 'name': 'Good QB', 'pos': 'QB', 'tm': 'BUF', 'points': 350},
            {'player_id': 'QB3', 'name': 'Average QB', 'pos': 'QB', 'tm': 'PHI', 'points': 300},
            {'player_id': 'QB4', 'name': 'Replacement QB', 'pos': 'QB', 'tm': 'DAL', 'points': 250},
            {'player_id': 'RB1', 'name': 'Elite RB', 'pos': 'RB', 'tm': 'SF', 'points': 300},
            {'player_id': 'RB2', 'name': 'Good RB', 'pos': 'RB', 'tm': 'BAL', 'points': 250},
            {'player_id': 'RB3', 'name': 'Average RB', 'pos': 'RB', 'tm': 'CIN', 'points': 200},
            {'player_id': 'RB4', 'name': 'Replacement RB', 'pos': 'RB', 'tm': 'PIT', 'points': 150},
        ]
        
        result = compute_replacement_and_vorp(players, cfg)
        
        # Check that all players have replacement points and VORP
        for player in result:
            assert 'repl_pts' in player
            assert 'vorp' in player
            assert 'pos_rank' in player
            assert 'overall_rank' in player
            
        # Check that players are ranked correctly
        qb_players = [p for p in result if p['pos'] == 'QB']
        qb_players.sort(key=lambda x: x['pos_rank'])
        
        assert qb_players[0]['name'] == 'Elite QB'
        assert qb_players[0]['pos_rank'] == 1
        assert qb_players[1]['name'] == 'Good QB'
        assert qb_players[1]['pos_rank'] == 2
        
        # Check VORP calculation (should be points - replacement_points)
        elite_qb = qb_players[0]
        assert elite_qb['vorp'] == elite_qb['points'] - elite_qb['repl_pts']
        assert elite_qb['vorp'] > 0  # Elite player should have positive VORP

    def test_compute_replacement_and_vorp_empty_position(self):
        """Test VORP calculation when a position has no players."""
        cfg = ScoringConfig()
        cfg.teams = 12
        cfg.roster = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1}
        cfg.flex_positions = ['RB', 'WR', 'TE']
        
        # Only QB players, no RB/WR/TE
        players = [
            {'player_id': 'QB1', 'name': 'Elite QB', 'pos': 'QB', 'tm': 'KC', 'points': 400},
            {'player_id': 'QB2', 'name': 'Good QB', 'pos': 'QB', 'tm': 'BUF', 'points': 350},
        ]
        
        result = compute_replacement_and_vorp(players, cfg)
        
        # Should still work without errors
        assert len(result) == 2
        for player in result:
            assert 'repl_pts' in player
            assert 'vorp' in player

    @patch('sklearn.cluster.KMeans')
    def test_add_tiers_kmeans_basic(self, mock_kmeans_class):
        """Test basic K-means tiering functionality."""
        # Mock KMeans
        mock_kmeans = Mock()
        mock_kmeans.fit.return_value = mock_kmeans
        mock_kmeans.labels_ = [0, 0, 1, 1, 2, 2, 3, 3]  # 4 tiers for 8 players
        mock_kmeans.cluster_centers_ = np.array([[150], [130], [100], [70]])  # VORP values
        mock_kmeans_class.return_value = mock_kmeans
        
        # Need 8+ players to trigger KMeans
        players = [
            {'player_id': 'QB1', 'name': 'Elite QB', 'pos': 'QB', 'points': 400, 'vorp': 150},
            {'player_id': 'QB2', 'name': 'Great QB', 'pos': 'QB', 'points': 380, 'vorp': 130},
            {'player_id': 'QB3', 'name': 'Good QB', 'pos': 'QB', 'points': 350, 'vorp': 100},
            {'player_id': 'QB4', 'name': 'Average QB', 'pos': 'QB', 'points': 320, 'vorp': 70},
            {'player_id': 'QB5', 'name': 'Below Average QB', 'pos': 'QB', 'points': 290, 'vorp': 40},
            {'player_id': 'QB6', 'name': 'Poor QB', 'pos': 'QB', 'points': 260, 'vorp': 20},
            {'player_id': 'QB7', 'name': 'Backup QB', 'pos': 'QB', 'points': 230, 'vorp': 10},
            {'player_id': 'QB8', 'name': 'Third String QB', 'pos': 'QB', 'points': 200, 'vorp': 5},
        ]
        
        result = add_tiers_kmeans(players)
        
        # Check that all players have tier assignments
        for player in result:
            assert 'tier' in player
            assert isinstance(player['tier'], int)
            assert player['tier'] >= 1  # Tiers should be 1-indexed
            
        # Check that KMeans was called for QB position
        mock_kmeans_class.assert_called()
        mock_kmeans.fit.assert_called()

    def test_add_tiers_kmeans_single_player(self):
        """Test tiering when a position has only one player."""
        players = [
            {'player_id': 'QB1', 'name': 'Only QB', 'pos': 'QB', 'points': 400, 'vorp': 150},
        ]
        
        result = add_tiers_kmeans(players)
        
        # Single player should get tier 1
        assert result[0]['tier'] == 1

    def test_add_tiers_kmeans_multiple_positions(self):
        """Test tiering across multiple positions."""
        players = [
            # QB players
            {'player_id': 'QB1', 'name': 'Elite QB', 'pos': 'QB', 'points': 400, 'vorp': 150},
            {'player_id': 'QB2', 'name': 'Good QB', 'pos': 'QB', 'points': 350, 'vorp': 100},
            # RB players  
            {'player_id': 'RB1', 'name': 'Elite RB', 'pos': 'RB', 'points': 300, 'vorp': 120},
            {'player_id': 'RB2', 'name': 'Good RB', 'pos': 'RB', 'points': 250, 'vorp': 70},
            # WR players
            {'player_id': 'WR1', 'name': 'Elite WR', 'pos': 'WR', 'points': 280, 'vorp': 100},
        ]
        
        result = add_tiers_kmeans(players)
        
        # Check that all players have tiers
        for player in result:
            assert 'tier' in player
            assert player['tier'] >= 1
            
        # Check that each position was processed
        positions = set(p['pos'] for p in result)
        assert positions == {'QB', 'RB', 'WR'}

    def test_add_tiers_kmeans_no_vorp_data(self):
        """Test tiering when players don't have VORP data."""
        players = [
            {'player_id': 'QB1', 'name': 'QB without VORP', 'pos': 'QB', 'points': 400, 'vorp': 0},
        ]
        
        result = add_tiers_kmeans(players)
        
        # Should still assign tier 1 to the only player
        assert result[0]['tier'] == 1

    @patch('sklearn.cluster.KMeans')
    def test_add_tiers_kmeans_empty_position_group(self, mock_kmeans_class):
        """Test that empty position groups are handled gracefully."""
        mock_kmeans = Mock()
        mock_kmeans.fit_predict.return_value = []
        mock_kmeans_class.return_value = mock_kmeans
        
        players = []  # Empty list
        
        result = add_tiers_kmeans(players)
        
        assert result == []
