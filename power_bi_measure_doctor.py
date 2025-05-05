#%%
from src.agents.agent_google import Agent
import src.prompts.power_bi_documentation as prompts
from dotenv import load_dotenv, find_dotenv
import os
from src.utils.utils import list_files_in_directory, update_measures_descriptions
import logging
import shutil
import json
from tkinter import filedialog
#%%

load_dotenv(find_dotenv())

google_api_key = os.getenv('GOOGLE_API_KEY')
# Create an instance of the Agent class
measure_prompt = prompts.get_prompt("power_bi_documentation")
power_bi_doctor = Agent(
    api_key=google_api_key,
    system_instruction=measure_prompt,
    
)

#load files to be used in the agent
# files_path = filedialog.askdirectory(
#     title="Select Directory with Power BI Models"
# )
files_path = r"C:\Users\micha\Documents\power bi challenge 21\Power BI Challenge 21 - “Enterprise DNA YouTube Channel Data Analysis”.SemanticModel"
model_files = list_files_in_directory(files_path, extension=".tmdl", recursive=True)

documentation_files = r"C:\Users\micha\Documents\power bi challenge 21\documentation"
documentation_files = list_files_in_directory(documentation_files,  recursive=True)
#define output schema

all_files = model_files + documentation_files


#%%
#get output from the agent
pbi_doctor_response = power_bi_doctor("I need descriptions for my measures",
files=model_files,
keep_chat_history=False,
#update_config=updated_config
)


#save the output to a file
# %%
output = json.loads(pbi_doctor_response.text.replace("```json\n", "").replace("```", ""))
mapping = output['descriptions']

path_parts = os.path.split(files_path)
back_up_folder = path_parts[-1] + "_backup"
back_up_path = os.path.join(*path_parts[:-1], back_up_folder)
shutil.copytree(files_path, back_up_path, dirs_exist_ok=True)

for file_path in model_files:
   with open(file_path, "r", encoding="utf-8") as f:
       file_content = f.read()
   updated_content = update_measures_descriptions(file_content, mapping)
   logging.info(f"Updated content for {file_path}")
   with open(file_path, "w", encoding="utf-8") as f:
       f.write(updated_content)
     
# %%
