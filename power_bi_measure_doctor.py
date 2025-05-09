import os
import logging
import shutil
import json
from tkinter import filedialog
import src.agents.powerBI_documenter_agent as pbi_doc_agent
from src.utils.utils import list_files_in_directory, update_measures_descriptions
import asyncio
import nest_asyncio

logging.basicConfig(level=logging.INFO)


async def get_measure_description(files_path: str):
    files_path = r"C:\Users\micha\Documents\power bi challenge 21\Power BI Challenge 21 - “Enterprise DNA YouTube Channel Data Analysis”.SemanticModel"
    model_files = list_files_in_directory(files_path, extension=".tmdl", recursive=True)

    deps = pbi_doc_agent.Deps(model_files)
    measure_descriptions = pbi_doc_agent.power_bi_agent.run_sync(
        "Measure descriptions", deps=deps
    )
    return measure_descriptions, model_files


if __name__ == "__main__":
    if os.environ.get("IS_LOCAL") == "1":
        nest_asyncio.apply()

    logging.info("Getting mode files from the directory")
    files_path = r"C:\Users\micha\Documents\power bi challenge 21\Power BI Challenge 21 - “Enterprise DNA YouTube Channel Data Analysis”.SemanticModel"
    logging.info("Getting measure descriptions from LLM")
    measure_descriptions, model_files = asyncio.run(get_measure_description(files_path))
    measure_descriptions = json.loads(
        measure_descriptions.output.replace("```json\n", "").replace("```", "")
    )
    logging.info("Measure descriptions received")

    files_path_parts = os.path.split(files_path)
    updated_folder = files_path_parts[-1] + "_updated"
    updated_folder = os.path.join(*files_path_parts[:-1], updated_folder)
    logging.info(f"Creating updated folder: {updated_folder}")
    shutil.copytree(files_path, updated_folder, dirs_exist_ok=True)

    logging.info(f"Updated folder created: {updated_folder}")

    logging.info("Updating measure descriptions in the model files")
    for file_path in model_files:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        updated_content = update_measures_descriptions(
            file_content, measure_descriptions
        )
        if updated_content != file_content:
            logging.info(f"Updated content for {file_path}")
        file_path = file_path.replace(files_path, updated_folder)
        # create the directory if it does not exist
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

# %%
