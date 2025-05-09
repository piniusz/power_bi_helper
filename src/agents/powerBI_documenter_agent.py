import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai import BinaryContent
from typing import List
from pathlib import Path
import os
import nest_asyncio
from src.utils.utils import list_files_in_directory
import logfire


model = GeminiModel("gemini-2.0-flash", provider="google-gla")


logfire.configure(send_to_logfire="if-token-present")

power_bi_agent_instructions = """
Your role is the Power BI Documentation Generator. You help users build excellent Power BI models and produce comprehensive documentation.

Always start by using the `get_model_context` tool to understand the model related to the user's question.

You are equipped to handle these tasks:

1.  **Answer Questions:** Provide information and answers about the user's Power BI model.
2.  **Write Measure Descriptions:** For every measure in the model, you will:
    * Write a short description (one or two sentences) that clearly explains the measure and its role. Vary your language and avoid starting every description the same way.

Deliver the measure descriptions as a JSON object. The measure name should be the key, and its description should be the value.

"""


@dataclass
class Deps:
    model_files: List[str | BinaryContent]
    business_ctx_files = List[str | BinaryContent] | None


power_bi_agent = Agent(
    model=model,
    system_prompt=power_bi_agent_instructions,
    deps_type=Deps,
    temperature=0,
    instrument=True,
)


@power_bi_agent.tool
async def get_model_context(ctx: RunContext[Deps]) -> list[BinaryContent]:
    """
    Get the model context from the provided files.
    """
    model_ctx = []
    mime_type_lookup = {"tmdl": "text/plain"}
    for file in ctx.deps.model_files:
        if type(file) == BinaryContent:
            model_ctx.append(file)
        else:
            file_extension = os.path.basename(file).split(".")[1]
            mime_type = mime_type_lookup.get(file_extension)
            if mime_type is None:
                raise TypeError(f"{file_extension} extentsion is not supported")
        file_path = Path(file)
        binary_content = file_path.read_bytes()
        binary_content = BinaryContent(binary_content, mime_type)
        model_ctx.append(binary_content)
    return model_ctx


if __name__ == "__main__":
    nest_asyncio.apply()
    gemini = Agent(model=model, temperature=0)
    models_files_path = r"C:\Users\micha\Documents\power bi challenge 21\Power BI Challenge 21 - “Enterprise DNA YouTube Channel Data Analysis”.SemanticModel"
    models_files = list_files_in_directory(models_files_path, ".tmdl", recursive=True)
    deps = Deps(models_files)
    results = power_bi_agent.run_sync("Measure descriptions", deps=deps)
