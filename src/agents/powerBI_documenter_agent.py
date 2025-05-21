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


model = GeminiModel("gemini-2.0-flash", provider="google-gla")

logfire.configure(send_to_logfire="if-token-present")

measure_documentation = """
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating documentation for DAX measures. Your primary goal is to produce a list of objects, each detailing a measure with its type, name, source, a varied description, and a confidence score.

**Mandatory Process for Generating Measure Documentation:**

1.  **FIRST ACTION (Tool Call - Get Measure Names):**
    * You **must make a tool call** to `get_model_elements_names`.
    * **Argument:** Provide `elementType: "measures"`.
    * **Purpose:** To retrieve the names of all DAX measures to be documented.

2.  **SECOND ACTION (Tool Call - Get Full Context):**
    * After receiving the measure names from the first tool call, you **must make a tool call** to `get_model_context`.
    * **Purpose:** To load all detailed Power BI model information and any relevant business context needed to understand and describe the measures.

3.  **THIRD ACTION (Generate JSON List of ObjectDetails):**
    * **Action:** For each measure identified from Tool Call 1, using the detailed model information from Tool Call 2, construct an object adhering to the `ObjectDetails` structure. The final output must be a single JSON array containing all these objects.
    * **Content Guidance for Each `ObjectDetails` instance (for a measure):**
        * `type` (string): Set to "measure".
        * `name` (string): The name of the current DAX measure.
        * `source` (string): Indicate the primary table this measure is logically associated with if clearly discernible (e.g., "Sales Table"). If it's ambiguous, not tied to a single table, or this information isn't available, use "Power BI Model".
        * `description` (string, 1-2 sentences):
            * Clearly explain the measure's conceptual calculation (what it achieves) AND its business purpose or the insight it provides. Avoid overly technical DAX.
            * **Critical for Quality - Varied Phrasing:** You **must** vary how you start each description. **Strictly avoid repeatedly using phrases like "This measure..."**.
            * **Techniques for Variety:** Consider starting with the measure's purpose (e.g., "To evaluate X..."), the insight it offers (e.g., "Key insight into Z is provided..."), a direct statement (e.g., "[Measure Name] quantifies X..."), or its calculation nature (e.g., "Calculating Y..."). Ensure natural language.
        * `confidence` (integer, 0-100): Your confidence score in the accuracy and completeness of the generated `description` based on the information you have.
    * **JSON Output Format:** A single JSON array, where each element is an object matching the `ObjectDetails` structure.
        ```json
        [
          {
            "type": "measure",
            "name": "Total Sales",
            "source_table": "Sales Table",
            "description": "Providing a key indicator of overall revenue, this measure calculates the sum of all sales amounts.",
            "confidence": 95
          },
          {
            "type": "measure",
            "name": "YoY Sales Growth",
            "source_table": "Power BI Model",
            "description": "Insight into sales performance trends is offered by this measure, determining the year-over-year growth percentage for total sales.",
            "confidence": 90
          }
        ]
        ```

**Critical Rule:** If either `get_model_elements_names` or `get_model_context` tool call fails, or if the retrieved data is insufficient to generate the documentation as requested, you must clearly state this issue (e.g., "Tool call `get_model_elements_names` with elementType 'measures' failed."). You should then return an empty list `[]` or an appropriate error object if your Pydantic AI agent handles errors in a specific way.
"""

column_documentation = """
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating documentation for Power BI columns. Your primary goal is to produce a list of objects, each detailing a column with its type, name, source (table name), a varied description, and a confidence score.

**Mandatory Process for Generating Column Documentation:**

1.  **FIRST ACTION (Tool Call - Get Column Names):**
    * You **must make a tool call** to `get_model_elements_names`.
    * **Argument:** Provide `elementType: "columns"`.
    * **Purpose:** To retrieve the names of columns to be documented, ideally structured by their parent tables if the tool supports this (e.g., the tool output might be `{"TableName1": ["ColA", "ColB"], "TableName2": ["ColC"]}`).

2.  **SECOND ACTION (Tool Call - Get Full Context):**
    * After receiving the column names/structure from the first tool call, you **must make a tool call** to `get_model_context`.
    * **Purpose:** To load all detailed Power BI model information and any relevant business context needed to understand and describe the columns.

3.  **THIRD ACTION (Generate JSON List of ObjectDetails):**
    * **Action:** For each column identified (within each table) from Tool Call 1, using the detailed model information from Tool Call 2, construct an object adhering to the `ObjectDetails` structure. The final output must be a single JSON array containing all these objects.
    * **Content Guidance for Each `ObjectDetails` instance (for a column):**
        * `type` (string): Set to "column".
        * `name` (string): The name of the current column.
        * `source` (string): The name of the table this column belongs to.
        * `description` (string, 1-2 sentences):
            * Clearly explain the column's data content AND its business meaning or role within its table.
            * **Critical for Quality - Varied Phrasing:** You **must** vary how you start each column description, especially for columns within the same table. **Strictly avoid repeatedly using phrases like "This column..."**.
            * **Techniques for Variety:** Consider starting with the data it holds (e.g., "Holding X values..."), its purpose (e.g., "Used to identify Y..."), or a direct statement (e.g., "[ColumnName] represents Z..."). Ensure natural language.
        * `confidence` (integer, 0-100): Your confidence score in the accuracy and completeness of the generated `description` based on the information you have (this replaces the previous `understanding_score`).
    * **JSON Output Format:** A single JSON array, where each element is an object matching the `ObjectDetails` structure.
        ```json
        [
          {
            "type": "column",
            "name": "CustomerID",
            "source_table": "DimCustomer",
            "description": "Uniquely identifying each customer, this field serves as the primary key for the DimCustomer table.",
            "confidence": 95
          },
          {
            "type": "column",
            "name": "CustomerName",
            "source_table": "DimCustomer",
            "description": "The full name of the customer is stored in this particular column.",
            "confidence": 90
          },
          {
            "type": "column",
            "name": "SalesAmount",
            "source": "FactSales",
            "description": "Representing the total monetary value of the sales transaction, this is a key financial metric.",
            "confidence": 95
          }
        ]
        ```

**Critical Rule:** If either `get_model_elements_names` or `get_model_context` tool call fails, or if the retrieved data is insufficient to generate the documentation as requested, you must clearly state this issue. You should then return an empty list `[]` or an appropriate error object.
"""

table_documentation = """
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating documentation for Power BI tables. Your primary goal is to produce a list of objects, each detailing a table with its type, name, source, a varied description, and a confidence score.

**Mandatory Process for Generating Table Documentation:**

1.  **FIRST ACTION (Tool Call - Get Table Names):**
    * You **must make a tool call** to `get_model_elements_names`.
    * **Argument:** Provide `elementType: "tables"`.
    * **Purpose:** To retrieve the names of all tables to be documented.

2.  **SECOND ACTION (Tool Call - Get Full Context):**
    * After receiving the table names from the first tool call, you **must make a tool call** to `get_model_context`.
    * **Purpose:** To load all detailed Power BI model information and any relevant business context needed to understand and describe the tables.

3.  **THIRD ACTION (Generate JSON List of ObjectDetails):**
    * **Action:** For each table identified from Tool Call 1, using the detailed model information from Tool Call 2, construct an object adhering to the `ObjectDetails` structure. The final output must be a single JSON array containing all these objects.
    * **Content Guidance for Each `ObjectDetails` instance (for a table):**
        * `type` (string): Set to "table".
        * `name` (string): The name of the current table.
        * `source` (string): Use "Power BI Model". If a specific schema name (other than default like 'dbo' or 'public') is known and relevant, you can use that (e.g., "Sales Schema").
        * `description` (string, 1-2 sentences):
            * Clearly describe the table's primary content AND its typical role in data analysis or the business model.
            * **Critical for Quality - Varied Phrasing:** You **must** vary how you start each description. **Strictly avoid repeatedly using phrases like "This table..."**.
            * **Techniques for Variety:** Consider starting with the table's main content (e.g., "Containing X data..."), its purpose/role (e.g., "For X analysis, this table serves to..."), or a direct statement (e.g., "[TableName] is a dimension/fact table that..."). Ensure natural language.
        * `confidence` (integer, 0-100): Your confidence score in the accuracy and completeness of the generated `description` based on the information you have (this replaces the previous `understanding_score`).
    * **JSON Output Format:** A single JSON array, where each element is an object matching the `ObjectDetails` structure.

**Critical Rule:** If either `get_model_elements_names` or `get_model_context` tool call fails, or if the retrieved data is insufficient to generate the documentation as requested, you must clearly state this issue. You should then return an empty list `[]` or an appropriate error object.
"""


@dataclass
class Deps:
    model_files: List[str | BinaryContent]
    business_ctx_files = List[str | BinaryContent] | None


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


async def call_agent(task: str, deps: Deps, output_schema=None) -> str:
    if task == "measure descriptions":
        system_prompt = measure_documentation
    elif task == "column descriptions":
        system_prompt = column_documentation
    elif task == "table descriptions":
        system_prompt = table_documentation
    else:
        raise ValueError(f"Unknown task: {task}")

    power_bi_agent = Agent(
        model=model,
        deps_type=Deps,
        system_prompt=system_prompt,
        temperature=0,
        instrument=True,
        output_type=ObjectDetailsList,
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

    @power_bi_agent.tool
    async def get_model_elements_names(
        ctx: RunContext[Deps], model_element: str
    ) -> Dict[str, list[str]]:
        """
        Get the names of specific elements from a Power BI model.

        This tool retrieves names of the specified type of elements (tables, measures, columns, etc.)
        from the Power BI model files provided in the context.

        Args:
          model_element (str): The type of model element to extract (e.g., "tables", "measures", "columns", "relationships").

        Returns:
          Dict[str, list[str]]: A dictionary mapping element types to lists of element names.

        Example:
          To get all table names:
          get_model_elements_names("tables")
          -> {"Sales.tmdl": ["Sales"]}

          To get all measure names:
          get_model_elements_names("measures")
          -> {"Measure table.tmdl": ["Total Sales", "YoY Growth", "Average Order Value"]}
        """
        files = ctx.deps.model_files

        model_elements = await get_objects_from_model(files, model_element)
        return model_elements

    result = power_bi_agent.run_sync(task, deps=deps)
    return result


# %%
class MeasureDocumentationOutput(BaseModel):
    """
    Output for measure documentation, with descriptions nested under a specific key.
    """

    measure_descriptions: Dict[str, str] = Field(
        ...,
        description="A dictionary mapping measure names to their textual descriptions.",
    )


if __name__ == "__main__":
    nest_asyncio.apply()
    gemini = Agent(model=model, temperature=0)
    models_files_path = r"C:\Users\micha\Documents\PBI files\competetive marketing analysis\Competitive Marketing Analysis.SemanticModel"
    models_files = list_files_in_directory(models_files_path, ".tmdl", recursive=True)
    deps = Deps(models_files)

    response = call_agent(
        task="measure descriptions",
        deps=deps,
    )


# %%
