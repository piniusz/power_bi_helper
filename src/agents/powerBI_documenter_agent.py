import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai import BinaryContent
from typing import List
from pathlib import Path
import os


model = GeminiModel("gemini-2.0-flash", provider="google-gla")

instructions = """
    You are a Power BI documentation generator. Your goal is to helps user with achieveing perect Power BI model and documentation.

    Depending on user request you can do several tasks:
    
    1.Answerw questions about a model
    2. Create measure descriptions:

    For each measure identified in the model, you will perform the following actions:

        1.  **Description Generation:**
            * Create a concise description of the measure, consisting of one to two sentences. This description should explain the measure and its purpose within the model. Aim for varied phrasing and avoid consistently starting descriptions with "This measure" to maintain a natural tone.

        Return the result as a JSON object (equivalent to a Python dictionary) where:
        - Each key is the exact name of a measure.
        - The corresponding value is the generated description for that measure.
"""


@dataclass
class Deps:
    model_files: List[str | BinaryContent]
    business_ctx_files = List[str | BinaryContent] | None


power_bi_agent = Agent(model=model, system_prompt=instructions, deps_type=Deps)


@power_bi_agent.tool
async def get_model_context(ctx: RunContext[Deps]) -> list[BinaryContent]:
    model_ctx = []
    mime_type_lookup = {"tmdl": "text/plain"}
    for file in ctx.model:
        if type(file) == BinaryContent:
            model_ctx.append(file)
        else:
            file_extension = os.path.basename(file).split(".")[1]
            mime_type = mime_type_lookup.get(file_extension)
            if mime_type is None:
                raise TypeError(f"{file_extension} extentsion is not supported")
        file_path = Path(file_path)
        binary_content = file_path.read_bytes()
        binary_content = BinaryContent(binary_content, mime_type)
        model_ctx.append(binary_content)
    return model_ctx


if __name__ == "__main__":
    gemini = Agent(model=model)
