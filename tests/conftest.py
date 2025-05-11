import sys
import os
import pytest
import tempfile
import shutil

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def test_case_paths():
    """Fixture to provide absolute paths to test case files."""
    test_case_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
    return {
        "measures_init": os.path.join(
            test_case_dir, "measure descriptions", "Init.tmdl"
        ),
        "measures_goal": os.path.join(
            test_case_dir, "measure descriptions", "Goal.tmdl"
        ),
        "columns_init": os.path.join(test_case_dir, "column descriptions", "Init.tmdl"),
        "columns_goal": os.path.join(test_case_dir, "column descriptions", "Goal.tmdl"),
        "model_folder": os.path.join(test_case_dir, "model fixtures"),
    }


@pytest.fixture
def test_directory():
    """Create a temporary directory with test files."""
    temp_dir = tempfile.mkdtemp()

    # Create files in the main directory
    with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
        f.write("content")
    with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
        f.write("content")
    with open(os.path.join(temp_dir, "file3.csv"), "w") as f:
        f.write("content")

    # Create a subdirectory with files
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    with open(os.path.join(subdir, "file4.txt"), "w") as f:
        f.write("content")
    with open(os.path.join(subdir, "file5.csv"), "w") as f:
        f.write("content")

    yield temp_dir

    # Clean up
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_agent_class(mocker):
    """Fixture to mock the Agent class."""
    mock_agent = mocker.patch("src.agents.agent.Agent")
    return mock_agent
