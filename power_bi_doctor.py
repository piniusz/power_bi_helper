# %%
import os
import logging
import shutil
from tkinter import filedialog
from src.agents.powerBI_documenter_agent import call_agent
from src.utils.utils import (
    list_files_in_directory,
    update_measures_columns_descriptions,
    update_table_description,
)
import asyncio
import nest_asyncio
from IPython import get_ipython

logging.basicConfig(level=logging.INFO)


async def get_model_documentation(
    analysis_requests: str,
    model_files_path: str,
    business_ctx_files_path: str = None,
):
    model_files = list_files_in_directory(
        model_files_path, extension=".tmdl", recursive=True
    )

    output = await call_agent(analysis_requests, model_files=model_files)

    return output, model_files


def process_documentation_results(results, requests):
    """
    Process the documentation results from the LLM and organize them by element type.

    Args:
        results: List of result tuples from model documentation requests
        requests: List of corresponding request strings

    Returns:
        dict: Organized documentation dictionary
    """
    documentation = {}

    for result, request in zip(results, requests):
        docs_list = result[0].output.objects_documentation
        if not docs_list:
            logging.warning(f"No documentation found for request: {request}")
            continue

        element_type = docs_list[0].type
        if element_type not in documentation:
            documentation[element_type] = {}

        # Delegate processing to specific handlers
        _process_element_type(documentation, element_type, docs_list)

    return documentation


def _process_element_type(documentation, element_type, docs_list):
    """Process documentation items based on their type."""
    processors = {
        "measure": _process_measures,
        "table": _process_tables,
        "column": _process_columns,
    }

    processor = processors.get(element_type)
    if processor:
        processor(documentation[element_type], docs_list)


def _process_measures(measure_docs, docs_list):
    """Process measure documentation items."""
    for item in docs_list:
        measure_docs[item.name] = {
            "description": item.description,
            "understanding_score": item.confidence,
        }


def _process_tables(table_docs, docs_list):
    """Process table documentation items."""
    for item in docs_list:
        table_name = item.name.split(".")[0]
        table_docs[table_name] = {
            "description": item.description,
            "understanding_score": item.confidence,
        }


def _process_columns(column_docs, docs_list):
    """Process column documentation items."""
    for item in docs_list:
        source_table = item.source_table.split(".")[0]

        if source_table not in column_docs:
            column_docs[source_table] = {}

        column_docs[source_table][item.name] = {
            "description": item.description,
            "understanding_score": item.confidence,
        }


async def main():
    logging.info("Getting mode files from the directory")
    files_path = (
        r"C:\Users\micha\Documents\PBI files\Store Sales\Store Sales.SemanticModel"
    )
    logging.info("Getting model documentation from LLM")
    requests = ["measure descriptions", "table descriptions", "column descriptions"]

    tasks = [get_model_documentation(req, files_path) for req in requests]
    results = await asyncio.gather(*tasks)
    model_files = results[0][1]
    # Process documentation results
    documentation = process_documentation_results(results, requests)

    logging.info("All documentation received")
    files_path_parts = os.path.split(files_path)

    updated_folder = files_path_parts[-1] + "_updated"
    updated_folder = os.path.join(*files_path_parts[:-1], updated_folder)

    logging.info(f"Creating updated folder: {updated_folder}")
    shutil.copytree(files_path, updated_folder, dirs_exist_ok=True)

    logging.info(f"Updated folder created: {updated_folder}")
    for file_path in model_files:
        table_name = os.path.basename(file_path).split(".")[0]
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            updated_file_content = file_content

        if "measure" in documentation.keys():
            measure_descriptions = documentation["measure"]
            updated_file_content = update_measures_columns_descriptions(
                updated_file_content, measure_descriptions, "measure"
            )
        if "table" in documentation.keys():
            table_descriptions = documentation["table"]
            if table_name in table_descriptions:
                description = table_descriptions[table_name]["description"]
                confidence = table_descriptions[table_name]["understanding_score"]
                if confidence > 0.8:
                    updated_file_content = update_table_description(
                        updated_file_content, description
                    )

        if "column" in documentation.keys():
            column_descriptions = documentation["column"]
            if table_name in column_descriptions.keys():
                column_descriptions = column_descriptions[table_name]

                updated_file_content = update_measures_columns_descriptions(
                    updated_file_content, column_descriptions, "column"
                )

        if updated_file_content != file_content:
            logging.info(f"Updated content for {file_path}")
            file_path = file_path.replace(files_path, updated_folder)
            # create the directory if it does not exist
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_file_content)


# %%
if __name__ == "__main__":
    if get_ipython() is not None:
        nest_asyncio.apply()
    asyncio.run(main())
# %%
