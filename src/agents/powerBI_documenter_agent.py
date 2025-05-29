# %%
import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers import openai
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import BinaryContent
from typing import List
from pathlib import Path
import os
import nest_asyncio
from src.utils.utils import (
    list_files_in_directory,
    get_objects_from_model,
)
import logfire
from typing import Dict, List
from pydantic import BaseModel, RootModel, Field
from typing import Dict

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
model = GeminiModel(GEMINI_MODEL, provider="google-gla")

logfire.configure(send_to_logfire="if-token-present")

documentation_prompt_template = """
{model_context}
{business_context}
<List of {object_type}'s>
{objects}
</List of {object_type}'s>
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating documentation for {object_type}s. 
Your primary goal is to produce a list of objects, each detailing a {object_type} with its type, name, source, a varied description, and a confidence score.

**Mandatory Process for Generating {object_type}'s Documentation:**


* **Action:** For each {object_type} in <List of {object_type}'s> tag, using detailed model context provided, construct an object adhering to the `ObjectDetails` structure. 
The final output must be a single JSON array containing all these objects.
* **Content Guidance for Each `ObjectDetails` instance:**
    * `type` (string): Set to "{object_type}".
    * `name` (string): The name of the current {object_type}.
    * `source_table` (string): 
        - For measures: Indicate the primary table this measure is logically associated with if clearly discernible. If ambiguous or not tied to a single table, use "Power BI Model".
        - For columns: Specify the table that contains this column.
        - For tables: Use the table name itself or "Power BI Model" if it's a calculated table.
    * `description` (string, 1-2 sentences):
        - For measures: Clearly explain the measure's conceptual calculation (what it achieves) AND its business purpose or the insight it provides. Avoid overly technical DAX.
        - For columns: Describe what data the column contains and its business relevance or purpose within the table.
        - For tables: Explain what business entity or data the table represents and its role in the data model.
        * **Critical for Quality - Varied Phrasing:** You **must** vary how you start each description. **Strictly avoid repeatedly using phrases like "This {object_type}..."**.
        * **Techniques for Variety:** Consider starting with the {object_type}'s purpose, the insight it offers, a direct statement, or its nature. Ensure natural language flow.
    * `confidence` (integer, 0-100): Your confidence score in the accuracy and completeness of the generated `description` based on the information you have.
* **JSON Output Format:** A single JSON array, where each element is an object matching the `ObjectDetails` structure.
    ```json
    [
        {{
        "type": "{object_type}",
        "name": "Example Name",
        "source_table": "Example Table",
        "description": "Example description with varied phrasing that explains the {object_type}'s purpose and business value." Start with a different phrase each time to keep it varied.
        "confidence": 95
        }}
    ]
    ```
"""


class ObjectDetails(BaseModel):
    type: str = Field(description="Type of object, e.g., table, measure, column")
    name: str = Field(description="Name of the object")
    source_table: str = Field(description="Source table of the object")
    description: str = Field(description="Description of the object")
    confidence: int = Field(
        description="Confidence score for the description, ranging from 0 to 100"
    )


class ObjectDetailsList(BaseModel):
    objects_documentation: List[ObjectDetails] = Field(
        ...,
        description="List of objects with their documentation details.",
    )


async def _prepare_model_context(model_files: list) -> str:
    """Prepare the model context from files with XML structure."""
    context_parts = []

    for file in model_files:
        if isinstance(file, str):
            file_path = Path(file)
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                context_parts.append(
                    f"<file name='{file_path.name}'>\n{content}\n</file>"
                )

    full_context = "\n".join(context_parts)
    return f"<model_context>\n{full_context}\n</model_context>"


async def call_agent(task: str, model_files: list, business_files: list = None) -> str:
    model_context = await _prepare_model_context(model_files)
    if task == "measure descriptions":
        object_type = "measure"
        objects = await get_objects_from_model(model_files, "measures")

    elif task == "column descriptions":
        object_type = "column"
        objects = await get_objects_from_model(model_files, "columns")

    elif task == "table descriptions":
        object_type = "table"
        objects = await get_objects_from_model(model_files, "tables")
    else:
        raise ValueError(f"Unknown task: {task}")

    system_prompt = documentation_prompt_template.format(
        model_context=model_context,
        business_context="",
        object_type=object_type,
        objects=objects,
    )

    power_bi_agent = Agent(
        model=model,
        system_prompt=system_prompt,
        temperature=0,
        instrument=True,
        output_type=ObjectDetailsList,
    )

    result = await power_bi_agent.run(task)
    return result


class MeasureDocumentationOutput(BaseModel):
    """
    Output for measure documentation, with descriptions nested under a specific key.
    """

    measure_descriptions: Dict[str, str] = Field(
        ...,
        description="A dictionary mapping measure names to their textual descriptions.",
    )


# %%
if __name__ == "__main__":
    nest_asyncio.apply()
    gemini = Agent(model=model, temperature=0)
    models_files_path = r"C:\Users\micha\Documents\PBI files\competetive marketing analysis\Competitive Marketing Analysis.SemanticModel"
    models_files = list_files_in_directory(models_files_path, ".tmdl", recursive=True)
    nest_asyncio.apply()
    response = asyncio.run(
        call_agent(
            task="measure descriptions",
            model_files=models_files,
        )
    )


# %%
