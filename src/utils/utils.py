import re

#%%

def update_measures_descriptions(file_content:str, mapping:dict)->str:
    """
    Update measure descriptions in the provided file content based on the mapping dictionary.

    Args:
        file_content (str): Content of the file to update.
        mapping (dict): Dictionary containing measure names as keys and descriptions as values.

    Returns:
        str: Updated file content with new measure descriptions.
    """
    file_content_updated = file_content

    # Update measure descriptions

    for measure_name, measure_description in mapping.items():
        # Capture measures with description
        pattern = rf"(?<=\t///)(.*?)([\S]*?)(?=\n\tmeasure '{re.escape(measure_name)}')"
        occurrence = re.findall(pattern, file_content_updated)
        file_content_updated = re.sub(pattern, f' {measure_description}', file_content_updated)

        # Capture measures without description
        pattern = rf"(?<=[\n\t]\n\t)(measure '?{re.escape(measure_name)}'? =)"
        occurrence = re.findall(pattern, file_content_updated)
        if len(occurrence) == 1:
            replacement = f"/// {measure_description}\n\t{occurrence[0]}"
            file_content_updated = re.sub(pattern, replacement, file_content_updated)
    #removing empty tabs
    pattern = r"\t+(?=\n)"
    file_content_updated = re.sub(pattern, "", file_content_updated)
    return file_content_updated