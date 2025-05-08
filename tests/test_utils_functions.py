import pytest
from src.utils import utils
import os
from pydantic_ai import BinaryContent
from pathlib import Path
from mock import patch, mock_open


def test_update_measures_descriptions_with_actual_files(test_case_paths):

    # Read the expected goal content
    with open(test_case_paths["goal_file"], "r", encoding="utf-8") as file:
        expected_content = file.read()
    with open(test_case_paths["init_file"], "r", encoding="utf-8") as file:
        file_content_raw = file.read()

    # Define the mapping
    mapping = {
        r"Measure 1": r"New description",
        r"Measure 2": r"New description",
        r"Measure_3": r"New description",
        r"Measure (4)": r"New description",
    }

    # Act

    updated_content = utils.update_measures_descriptions(file_content_raw, mapping)

    # Assert that the updated content matches the expected content
    assert updated_content == expected_content  #


def test_list_files_in_directory(test_directory):
    """Test the list_files_in_directory function with a temporary directory."""
    # Test listing files in the main directory
    files = utils.list_files_in_directory(test_directory, extension=".txt")
    assert len(files) == 2  # 2 in main dir
    assert all(file.endswith(".txt") for file in files)

    # Test listing files recursively
    recursive_files = utils.list_files_in_directory(
        test_directory, extension=".txt", recursive=True
    )
    assert len(recursive_files) == 3  # 2 in main dir + 1 in subdir
    assert all(file.endswith(".txt") for file in recursive_files)

    # Test listing all files without extension filter
    all_files = utils.list_files_in_directory(test_directory)
    assert len(all_files) == 3  # All files in main directory

    # Test listing files with a different extension
    csv_files = utils.list_files_in_directory(
        test_directory, extension=".csv", recursive=True
    )
    assert len(csv_files) == 2  # Only the .csv files
