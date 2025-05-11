# %%
import os
import logging
import shutil
import json
from tkinter import filedialog
from src.agents.powerBI_documenter_agent import call_agent, Deps
from src.utils.utils import (
    list_files_in_directory,
    update_measures_columns_descriptions,
    update_table_description,
)
import asyncio
import nest_asyncio
from pydantic_ai.models.gemini import GeminiModel, ThinkingConfig
import re

logging.basicConfig(level=logging.INFO)


async def get_model_documentation(
    model_files_path: str,
    analysis_requests: str,
    business_ctx_files_path: str = None,
):
    model_files = list_files_in_directory(
        model_files_path, extension=".tmdl", recursive=True
    )
    deps = Deps(model_files)
    if business_ctx_files_path:
        business_files = model_files = list_files_in_directory(
            business_ctx_files_path, recursive=True
        )
        deps = Deps(model_files, business_files)

    output = call_agent(analysis_requests, deps=deps)

    return output, model_files


# %%
if __name__ == "__main__":
    if os.environ.get("IS_LOCAL") == "1":
        nest_asyncio.apply()

    logging.info("Getting mode files from the directory")
    files_path = r"C:\Users\micha\Documents\PBI files\competetive marketing analysis\Competitive Marketing Analysis.SemanticModel"
    logging.info("Getting model documentation from LLM")
    requests = ["measure descriptions", "table descriptions", "column descriptions"]
    # requests = ["measure descriptions"]

    final_output = {}
    model = "gemini-2.5-flash-preview-04-17"

    async def process_request(request):
        """Process a single documentation request and parse the result"""
        logging.info(f"Processing request: {request}")
        llm_output, model_files = await get_model_documentation(
            files_path,
            request,
        )

        pattern = r"```json\s*([\s\S]*?)\s*```"
        json_match = re.search(pattern, llm_output.output)
        json_str = json_match.group(1)
        parsed_output = json.loads(
            json_str.replace("```json\n", "").replace("```", "").replace(".tmdl", "")
        )

        return request, parsed_output, model_files

    async def run_parallel_requests():
        """Run all requests in parallel and collect results"""
        tasks = [process_request(request) for request in requests]
        results = await asyncio.gather(*tasks)

        final_output = {}
        # Collect results and the model_files
        for request, output, model_files in results:
            final_output[request.replace(" ", "_")] = output

        return final_output, model_files

    # Run all requests in parallel
    final_output, model_files = asyncio.run(run_parallel_requests())

    logging.info("All documentation received")
    files_path_parts = os.path.split(files_path)

    updated_folder = files_path_parts[-1] + "_updated"
    updated_folder = os.path.join(*files_path_parts[:-1], updated_folder)

    logging.info(f"Creating updated folder: {updated_folder}")
    shutil.copytree(files_path, updated_folder, dirs_exist_ok=True)

    logging.info(f"Updated folder created: {updated_folder}")
    # %%
    for file_path in model_files:
        table_name = os.path.basename(file_path).split(".")[0]
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            updated_file_content = file_content

        if "measure_descriptions" in final_output.keys():
            measure_descriptions = final_output["measure_descriptions"]
            updated_file_content = update_measures_columns_descriptions(
                updated_file_content, measure_descriptions, "measure"
            )
        # if "table_descriptions" in final_output.keys():
        #     table_descriptions = final_output["table_descriptions"]
        #     if table_name in table_descriptions:
        #         description = table_descriptions[table_name]["description"]
        #         confidence = table_descriptions[table_name]["understanding_score"]
        #         if confidence > 0.8:
        #             updated_file_content = update_table_description(
        #                 updated_file_content, description
        #             )

        if "column_descriptions" in final_output.keys():
            column_descriptions = final_output["column_descriptions"]
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
