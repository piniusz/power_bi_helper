#%%
from src.agents.agent_google import Agent
import src.prompts.power_bi_documentation as prompts
from dotenv import load_dotenv, find_dotenv
import os
from src.utils.utils import list_files_in_directory
from io import BytesIO
import logging
from google.genai import types
import pydantic
import json
from typing import Dict, Any, Optional, List, Union
#%%

load_dotenv(find_dotenv())

google_api_key = os.getenv('GOOGLE_API_KEY')
log = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

# Create an instance of the Agent class
measure_prompt = prompts.get_prompt("power_bi_documentation")
power_bi_doctor = Agent(
    api_key=google_api_key,
    system_instruction=measure_prompt,
    
)

#load files to be used in the agent
files_path = r"test_data"
model_files = list_files_in_directory(files_path, extension=".tmdl", recursive=True)
#define output schema
#%%
class MeasureDescription(pydantic.BaseModel):
    descriptions: Dict[str, str] 
output_schema = {
    "type": "object",
    # The description for the object itself is fine here
    "description": "A dictionary where keys are measure names and values are their descriptions.",
    "additionalProperties": {
        "type": "string"
        # Removed: "description": "The description of the measure."
        # This dictionary just defines the schema for the VALUE allowed for additional properties
    }
}



#%%
#get output from the agent
pbi_doctor_response = power_bi_doctor("I need descriptions for my measures",
files=model_files,
keep_chat_history=True,
#update_config=updated_config
)


#save the output to a file
# %%
output = json.loads(pbi_doctor_response.text.replace("```json\n", "").replace("```", ""))


# %%
