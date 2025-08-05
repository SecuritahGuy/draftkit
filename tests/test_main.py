import pytest
from unittest.mock import Mock, patch

# Test the main module entry point
def test_main_module():
    """Test that the main module can be imported without executing CLI."""
    # Import the cli module first to avoid execution
    with patch('draftkit.cli.app') as mock_app:
        import draftkit.__main__
        # The app() call should have been made during import
        mock_app.assert_called_once()

def test_main_module_structure():
    """Test that the main module has the expected structure."""
    # Test importing the module without triggering execution
    with patch('sys.argv', ['draftkit']):  # Mock sys.argv to avoid CLI execution
        with patch('draftkit.cli.app') as mock_app:
            import importlib
            import draftkit.__main__
            # Reload to ensure fresh import
            importlib.reload(draftkit.__main__)
            assert True  # If we get here, import succeeded
