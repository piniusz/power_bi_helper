import src.prompts.power_bi_documentation as prompts
from dotenv import load_dotenv, find_dotenv
import os
from src.utils.utils import (
    list_files_in_directory,
    update_measures_descriptions,
    load_file_to_binary,
)
import logging
import shutil
import json
from tkinter import filedialog
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel
from pathlib import Path
import nest_asyncio
from pydantic import BaseModel, Field
from typing import Dict, Optional

# Create an instance of the Agent class
nest_asyncio.apply()

measure_prompt = prompts.get_prompt("power_bi_documentation")
model = GeminiModel("gemini-2.0-flash", provider="google-gla")
power_bi_doctor = Agent(system_prompt=measure_prompt, model=model, temperature=0.2)
# load files to be used in the agent
# files_path = filedialog.askdirectory(title="Select Directory with Power BI Models")
files_path = r"C:\Users\mkonieczny\OneDrive - KPMG\Documents\PBIP Sample\Sales & Returns Sample v201912.SemanticModel"
model_files = list_files_in_directory(files_path, extension=".tmdl", recursive=True)

# documentation_files = r"C:\Users\micha\Documents\power bi challenge 21\documentation"
# documentation_files = list_files_in_directory(documentation_files,  recursive=True)

# get output from the agent

model_ctx = ["Model files:"]
files_binary = load_file_to_binary(model_files)
model_ctx = model_ctx + files_binary

response = power_bi_doctor.run_sync(model_ctx)


# save the output to a file
# %%
output = json.loads(response.output.replace("```json\n", "").replace("```", ""))
mapping = output["descriptions"]

path_parts = os.path.split(files_path)
updated_folder = path_parts[-1] + "_updated"
updated_folder = os.path.join(*path_parts[:-1], updated_folder)
shutil.copytree(files_path, updated_folder, dirs_exist_ok=True)

for file_path in model_files:
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    updated_content = update_measures_descriptions(file_content, mapping)
    logging.info(f"Updated content for {file_path}")
    file_path = file_path.replace(files_path, updated_folder)
    # create the directory if it does not exist
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

# %%
