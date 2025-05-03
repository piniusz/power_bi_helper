import os
import pytest
from src.utils import utils

def test_update_measures_descriptions_with_actual_files(test_case_paths):
    
    # Read the expected goal content
    with open(test_case_paths['goal_file'], 'r', encoding='utf-8') as file:
        expected_content = file.read()
    with open(test_case_paths['init_file'], 'r', encoding='utf-8') as file:
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
    assert updated_content == expected_content #


