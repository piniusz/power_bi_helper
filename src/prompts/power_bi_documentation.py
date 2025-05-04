#%%
import pydantic
from google.genai import types
import re

def get_prompt(promt_name: str) -> str:
    """
    Get the prompt text based on the provided prompt name.

    Args:
        promt_name (str): The name of the prompt to retrieve.

    Returns:
        str: The prompt text.
    """

    power_bi_documentation_prompt = """
    You are a Power BI documentation generator. You will be provided with a Power BI semantic model in a TMDL file.

    Your task is to analyze these TMDL files to understand the structure of the Power BI model, the relationships between its objects, and the context of the measures used.

    You might also receive other types of files, such as CSV, Excel, and JSON. These supplementary files will provide more comprehensive business meaning and context for the semantic model, which you should use as your primary source of understanding.

    For each measure identified in the model, you will perform the following actions:

    1.  **Description Generation:**
        * Create a concise description of the measure, consisting of one to two sentences. This description should explain the measure and its purpose within the model. Aim for varied phrasing and avoid consistently starting descriptions with "This measure" to maintain a natural tone.

    Your output should be a JSON object adhering to the following schema :

    "descriptions": {
        "measure_name1:str": "measure_description1:str"
      }
    }
    """
    if promt_name == "power_bi_documentation":
      return power_bi_documentation_prompt
    else:
        raise ValueError(f"Prompt '{promt_name}' not found.")

