"""
Player overrides system for rookies and role changes.

Allows manual point overrides for players that blended projections can't handle well,
such as rookies with no NFL history or players in significantly new roles.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def load_overrides(override_path: Path) -> pd.DataFrame:
    """
    Load player overrides from CSV file.
    
    Args:
        override_path: Path to CSV file with columns: player_id, name, pos, tm, points, note
        
    Returns:
        DataFrame with override data, empty if file doesn't exist or has issues
    """
    if not override_path.exists():
        logger.info(f"No override file found at {override_path}")
        return pd.DataFrame()
    
    try:
        overrides = pd.read_csv(override_path)
        
        # Validate required columns
        required_cols = ['player_id', 'name', 'pos', 'tm', 'points']
        missing_cols = [col for col in required_cols if col not in overrides.columns]
        if missing_cols:
            logger.warning(f"Override file missing required columns: {missing_cols}")
            return pd.DataFrame()
        
        # Optional note column
        if 'note' not in overrides.columns:
            overrides['note'] = ''
        
        # Validate data types
        overrides['points'] = pd.to_numeric(overrides['points'], errors='coerce')
        overrides = overrides.dropna(subset=['points'])
        
        logger.info(f"Loaded {len(overrides)} player overrides from {override_path}")
        return overrides
        
    except Exception as e:
        logger.error(f"Error loading overrides from {override_path}: {e}")
        return pd.DataFrame()


def apply_overrides(players: List[Dict[str, Any]], override_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Apply player overrides to the players list.
    
    Args:
        players: List of player dictionaries with standard fantasy data
        override_path: Path to CSV override file, if provided
        
    Returns:
        Updated players list with overrides applied and source field added
    """
    if not override_path or not override_path.exists():
        # Add source field to all players as 'blend' (default)
        for player in players:
            player['source'] = 'blend'
        return players
    
    # Load overrides
    overrides_df = load_overrides(override_path)
    if overrides_df.empty:
        # Add source field as 'blend' if no overrides loaded
        for player in players:
            player['source'] = 'blend'
        return players
    
    # Convert players to DataFrame for easier processing
    players_df = pd.DataFrame(players)
    
    # Create override lookup by player_id
    override_lookup = {}
    for _, row in overrides_df.iterrows():
        override_lookup[row['player_id']] = {
            'points': row['points'],
            'note': row.get('note', ''),
            'override_name': row['name'],  # For verification
            'override_pos': row['pos'],
            'override_tm': row['tm']
        }
    
    # Apply overrides
    overrides_applied = 0
    for i, player in enumerate(players):
        player_id = player.get('player_id')
        
        if player_id and player_id in override_lookup:
            override_data = override_lookup[player_id]
            
            # Apply the override
            original_points = player.get('points', 0)
            player['points'] = override_data['points']
            player['source'] = 'override'
            player['override_note'] = override_data['note']
            
            # Log the override for transparency
            logger.info(f"Override applied: {player.get('name', 'Unknown')} "
                       f"({player.get('pos', 'N/A')}) - "
                       f"{original_points:.1f} → {override_data['points']:.1f} pts")
            
            overrides_applied += 1
        else:
            # Mark as blend source
            player['source'] = 'blend'
    
    logger.info(f"Applied {overrides_applied} player overrides")
    return players


def create_sample_overrides_2025(output_path: Path) -> None:
    """
    Create a sample overrides file for 2025 rookies and key role changes.
    
    Args:
        output_path: Where to write the sample CSV file
    """
    # 2025 rookie projections and key role changes
    # Note: These are example projections - adjust based on your league's scoring and expectations
    sample_overrides = [
        {
            'player_id': '00-0037013',  # Caleb Williams (example ID)
            'name': 'Caleb Williams',
            'pos': 'QB',
            'tm': 'CHI',
            'points': 285.0,
            'note': '2024 #1 overall pick, expected starter with rushing upside'
        },
        {
            'player_id': '00-0037019',  # Marvin Harrison Jr. (example ID)  
            'name': 'Marvin Harrison Jr.',
            'pos': 'WR',
            'tm': 'ARI',
            'points': 215.0,
            'note': '2024 #4 overall pick, elite college production, immediate WR1 role'
        },
        {
            'player_id': '00-0037021',  # Rome Odunze (example ID)
            'name': 'Rome Odunze',
            'pos': 'WR', 
            'tm': 'CHI',
            'points': 180.0,
            'note': '2024 #9 overall pick, strong college metrics, WR2 role in Chicago'
        },
        {
            'player_id': '00-0037025',  # Jayden Daniels (example ID)
            'name': 'Jayden Daniels',
            'pos': 'QB',
            'tm': 'WAS',
            'points': 275.0,
            'note': '2024 #2 overall pick, dual-threat QB with rushing floor'
        },
        {
            'player_id': '00-0037018',  # Drake Maye (example ID)
            'name': 'Drake Maye',
            'pos': 'QB',
            'tm': 'NE',
            'points': 245.0,
            'note': '2024 #3 overall pick, may start mid-season'
        },
        # Add more rookies and role changes as needed
    ]
    
    # Convert to DataFrame and save
    overrides_df = pd.DataFrame(sample_overrides)
    overrides_df.to_csv(output_path, index=False)
    
    print(f"Created sample 2025 overrides file at {output_path}")
    print(f"Contains {len(sample_overrides)} player overrides")
    print("\nSample entries:")
    for i, player in enumerate(sample_overrides[:3], 1):
        print(f"{i}. {player['name']} ({player['pos']}, {player['tm']}) - {player['points']} pts")
    print("...")


def validate_overrides(override_path: Path, players: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate override file against current player data.
    
    Args:
        override_path: Path to override CSV file
        players: Current players list to validate against
        
    Returns:
        Dictionary with validation results and warnings
    """
    if not override_path.exists():
        return {'valid': True, 'warnings': [], 'errors': []}
    
    overrides_df = load_overrides(override_path)
    if overrides_df.empty:
        return {'valid': False, 'warnings': [], 'errors': ['Could not load override file']}
    
    # Create player lookup for validation
    player_lookup = {p.get('player_id'): p for p in players if p.get('player_id')}
    
    warnings = []
    errors = []
    
    for _, override in overrides_df.iterrows():
        player_id = override['player_id']
        
        # Check if player exists in current data
        if player_id not in player_lookup:
            warnings.append(f"Override for {override['name']} ({player_id}) - player not found in current data")
        else:
            # Validate basic info matches
            player = player_lookup[player_id]
            if player.get('pos') != override['pos']:
                warnings.append(f"Position mismatch for {override['name']}: "
                               f"override={override['pos']}, data={player.get('pos')}")
            if player.get('tm') != override['tm']:
                warnings.append(f"Team mismatch for {override['name']}: "
                               f"override={override['tm']}, data={player.get('tm')}")
        
        # Validate points are reasonable
        points = override['points']
        if points < 0:
            errors.append(f"Negative points for {override['name']}: {points}")
        elif points > 500:  # Sanity check for fantasy points
            warnings.append(f"Very high points for {override['name']}: {points}")
    
    return {
        'valid': len(errors) == 0,
        'warnings': warnings,
        'errors': errors,
        'override_count': len(overrides_df)
    }
