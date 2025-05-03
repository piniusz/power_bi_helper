import sys
import os
import pytest

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def test_case_paths():
    """Fixture to provide absolute paths to test case files."""
    test_case_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
    return {
        'init_file': os.path.join(test_case_dir, 'Measure table initial.tmdl'),
        'goal_file': os.path.join(test_case_dir, 'Measure table goal.tmdl')
    }