import re
import os
from pathlib import Path
from pydantic_ai import BinaryContent
from typing import List


def update_measures_columns_descriptions(
    file_content: str, mapping: dict, object_to_map: str
) -> str:
    """
    Updates or adds descriptions for measures or columns in a Power BI model file.

    This function processes the content of a Power BI model file and updates existing
    descriptions or adds new descriptions for measures or columns based on the provided mapping.

    Args:
        file_content (str): The content of the Power BI model file.
        mapping (dict): A dictionary mapping object names to their descriptions.
                        Format: {object_name: object_description}
        object_to_map (str): The type of object to update descriptions for.
                            Must be either 'measure' or 'column'.

    Returns:
        str: The updated content of the Power BI model file with updated descriptions.

    Raises:
        Exception: If object_to_map is not 'measure' or 'column'.

    Example:
        >>> mapping = {"Sales": "Total sales amount", "Profit": "Net profit"}
        >>> updated_content = update_measures_columns_descriptions(file_content, mapping, "measure")
    """

    updated_content = file_content
    if object_to_map not in ["measure", "column"]:
        raise Exception("object_to_map must be either 'measure' or 'column'")
    # Update measure descriptions based on the provided mapping
    for object_name, content in mapping.items():
        # Find and replace existing measure descriptions
        object_description = content["description"]
        understanding_score = content["understanding_score"]
        # if understanding_score < 0.8:
        #     continue

        existing_desc_pattern = rf"(?<=\t///)(.*?)([\S]*?)(?=\n\t{object_to_map} '{re.escape(object_name)}')"
        updated_content = re.sub(
            existing_desc_pattern, f" {object_description}", updated_content
        )

        # Find measures without descriptions and add new descriptions
        no_desc_pattern = (
            rf"(?<=[\n\t]\n\t)({object_to_map} '?{re.escape(object_name)}'?)(?=\n| =)"
        )
        no_desc_matches = re.findall(no_desc_pattern, updated_content)
        if len(no_desc_matches) == 1:
            replacement = f"/// {object_description}\n\t{no_desc_matches[0]}"
            updated_content = re.sub(no_desc_pattern, replacement, updated_content)

    # Remove empty tabs at the end of lines
    empty_tabs_pattern = r"\t+(?=\n)"
    updated_content = re.sub(empty_tabs_pattern, "", updated_content)

    return updated_content


def update_table_description(file_content: str, description: str) -> str:
    """
    Updates or adds a description for a table in a Power BI model file.

    This function processes the content of a Power BI model file and updates
    an existing table description or adds a new description if none exists.

    Args:
        file_content (str): The content of the Power BI model file.
        description (str): The description to add or update for the table.

    Returns:
        str: The updated content of the Power BI model file with the updated table description.

    Example:
        >>> updated_content = update_table_description(file_content, "Customer information table")
    """
    existing_desc_pattern = r"(?<=///)(.*?)([\S]*?)(?=\ntable)"
    search = re.search(existing_desc_pattern, file_content)
    if search is not None:
        updated_content = re.sub(existing_desc_pattern, description, file_content)
    else:
        updated_content = f"/// {description}\n" + file_content
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


async def get_objects_from_model(model_files: List[str], model_element: str) -> dict:
    """
    Extracts object names of specified type from multiple Power BI tabular model files.

    This function uses regular expressions to find and extract names of objects
    from Power BI tabular model files based on the specified model element type.

    Args:
        model_files (List[str]): List of file paths to Power BI model files (.tmdl).
        model_element (str): The type of model element to extract. Must be one of:
                             'measures', 'columns', or 'tables'.

    Returns:
        dict: A dictionary where keys are file names and values are lists of object names found in each file.
              Names are normalized to handle escaped single quotes.

    Raises:
        Exception: If model_element is not one of the supported types.

    Example:
        >>> model_files = list_files_in_directory("path/to/models", "tmdl")
        >>> tables = get_objects_from_model(model_files, "tables")
    """
    all_objects = {}
    patterns = {
        "measures": r"(?<=\n\tmeasure )(?:'((?:[^']|'')*)'|([^\s'=]+))(?= \=)",
        "columns": r"(?<=\n\tcolumn )(?:'((?:[^']|'')*)'|([^\s'=]+))(?=\n| =)",
        "tables": r"(?<=table )(?:'((?:[^']|'')*)'|([^\s'=]+))(?=\n)",
    }
    for file in model_files:
        if not file.endswith(".tmdl"):
            raise TypeError(f"{file} is not a .tmdl file")
        # Read the file content

        with open(file, "r", encoding="utf-8") as f:
            model_ct = f.read()
        # Find the table name
        file_name = os.path.basename(file)

        pattern = patterns.get(model_element)
        if pattern is None:
            raise Exception("Unknown model element")

        matches = re.findall(pattern, model_ct)
        matches = [match for match in matches if match[0] or match[1]]
        # Extract the object names from the matches
        # The first group is the name with single quotes, the second is without
        # We want to use the first one if it exists, otherwise the second one
        objects = [match[0] if match[0] else match[1] for match in matches]

        if objects:
            all_objects[file_name] = objects

    return all_objects


def concatenate_files_content(files_path: list, file_encoding: str = None) -> str:
    files_content = []
    for file in files_path:
        with open(file, "r", encoding=file_encoding) as f:
            files_content.append(f.read())
    files_content_str = "\n".join(files_content)
    return files_content_str


if __name__ == "__main__":
    path = r"C:\Users\micha\Documents\PBI files\competetive marketing analysis\Competitive Marketing Analysis.SemanticModel"
    files = list_files_in_directory(path, "tmdl", recursive=True)
    content = concatenate_files_content(files)
    measures_list = get_objects_from_model(content, "measure")
