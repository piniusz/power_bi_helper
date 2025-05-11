import pytest
from src.utils import utils
import os
from pydantic_ai import BinaryContent
from pathlib import Path


def test_update_measures_descriptions_with_actual_files(test_case_paths):

    # Read the expected goal content
    with open(test_case_paths["measures_goal"], "r", encoding="utf-8") as file:
        expected_content = file.read()
    with open(test_case_paths["measures_init"], "r", encoding="utf-8") as file:
        file_content_raw = file.read()

    # Define the mapping
    mapping = {
        r"Measure 1": {"description": "New description", "understanding_score": 0.9},
        r"Measure 2": {"description": "New description", "understanding_score": 0.9},
        r"Measure_3": {"description": "New description", "understanding_score": 0.9},
        r"Measure (4)": {"description": "New description", "understanding_score": 0.9},
    }

    # Act

    updated_content = utils.update_measures_columns_descriptions(
        file_content_raw, mapping, "measure"
    )

    # Assert that the updated content matches the expected content
    assert updated_content == expected_content  #


def test_update_columns_descriptions_with_actual_files(test_case_paths):

    # Read the expected goal content
    with open(test_case_paths["columns_goal"], "r", encoding="utf-8") as file:
        expected_content = file.read()
    with open(test_case_paths["columns_init"], "r", encoding="utf-8") as file:
        file_content_raw = file.read()

    # Define the mapping
    mapping = {
        r"Video ID": {"description": "New description", "understanding_score": 0.9},
        r"Duration": {"description": "New description", "understanding_score": 0.9},
        r"Video name": {"description": "New description", "understanding_score": 0.9},
        r"Views total": {"description": "New description", "understanding_score": 0.9},
        r"Views": {"description": "New description", "understanding_score": 0.9},
    }

    # Act

    updated_content = utils.update_measures_columns_descriptions(
        file_content_raw, mapping, "column"
    )

    # Assert that the updated content matches the expected content
    assert updated_content == expected_content


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


def test_tmdl_object_finder(test_case_paths):
    # Arrange
    model_files = utils.list_files_in_directory(
        test_case_paths["model_folder"], extension=".tmdl", recursive=True
    )

    expected_measures = {"KPI.tmdl": ["KPI01", "KPI 02", "new''s measure"]}
    expected_columns = {
        "KPI.tmdl": ["KPI''s name", "Category", "Category name"],
        "Videos.tmdl": ["Video ID", "Duration", "Video name"],
    }
    expected_tables = {"KPI.tmdl": ["KPI"], "Videos.tmdl": ["Videos"]}

    found_columns = utils.get_objects_from_model(model_files, "columns")
    found_measures = utils.get_objects_from_model(model_files, "measures")
    found_tables = utils.get_objects_from_model(model_files, "tables")

    # Assert
    assert found_measures == expected_measures
    assert found_columns == expected_columns
    assert found_tables == expected_tables
