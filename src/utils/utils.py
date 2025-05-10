import re
import os
from pathlib import Path
from pydantic_ai import BinaryContent


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
    for object_name, object_description in mapping.items():
        # Find and replace existing measure descriptions

        existing_desc_pattern = rf"(?<=\t///)(.*?)([\S]*?)(?=\n\t{object_to_map} '{re.escape(object_name)}')"
        updated_content = re.sub(
            existing_desc_pattern, f" {object_description}", updated_content
        )

        # Find measures without descriptions and add new descriptions
        no_desc_pattern = (
            rf"(?<=[\n\t]\n\t)({object_to_map} '?{re.escape(object_name)}'?)"
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
