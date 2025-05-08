import re
import os
from pathlib import Path
from pydantic_ai import BinaryContent


def update_measures_descriptions(file_content: str, mapping: dict) -> str:
    """
    Update measure descriptions in the provided file content based on the mapping dictionary.

    Args:
        file_content (str): Content of the file to update.
        mapping (dict): Dictionary containing measure names as keys and descriptions as values.

    Returns:
        str: Updated file content with new measure descriptions.
    """
    updated_content = file_content

    # Update measure descriptions based on the provided mapping
    for measure_name, measure_description in mapping.items():
        # Find and replace existing measure descriptions
        existing_desc_pattern = (
            rf"(?<=\t///)(.*?)([\S]*?)(?=\n\tmeasure '{re.escape(measure_name)}')"
        )
        updated_content = re.sub(
            existing_desc_pattern, f" {measure_description}", updated_content
        )

        # Find measures without descriptions and add new descriptions
        no_desc_pattern = rf"(?<=[\n\t]\n\t)(measure '?{re.escape(measure_name)}'? =)"
        no_desc_matches = re.findall(no_desc_pattern, updated_content)
        if len(no_desc_matches) == 1:
            replacement = f"/// {measure_description}\n\t{no_desc_matches[0]}"
            updated_content = re.sub(no_desc_pattern, replacement, updated_content)

    # Remove empty tabs at the end of lines
    empty_tabs_pattern = r"\t+(?=\n)"
    updated_content = re.sub(empty_tabs_pattern, "", updated_content)

    return updated_content


def list_files_in_directory(
    directory: str, extension: str = None, recursive: bool = False
) -> list:
    """
    List all files in a directory with a specific extension.

    Args:
        directory (str): The directory to search in.
        extension (str, optional): The file extension to filter by. If None, all files are listed.
        recursive (bool, optional): Whether to search recursively in subdirectories.

    Returns:
        list: A list of file paths matching the criteria.
    """
    if recursive:
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(directory)
            for file in files
            if not extension or file.endswith(extension)
        ]
    else:
        return [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if (not extension or file.endswith(extension))
            and os.path.isfile(os.path.join(directory, file))
        ]


def load_file_to_binary(file_list: list[str]):
    files_binary = []
    for file_path in file_list:
        file_extension = os.path.basename(file_path).split(".")[1]
        if file_extension == "tmdl":
            file_path = Path(file_path)
            file_bytes = file_path.read_bytes()
            file_binary = BinaryContent(file_bytes, media_type="text/plain")
            files_binary.append(file_binary)
        else:
            raise TypeError(f"{file_extension} is unsupported datatype")
    return files_binary
