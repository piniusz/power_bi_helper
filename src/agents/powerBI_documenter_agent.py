# %%
import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel, GeminiModelSettings
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
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating DAX measure documentation. Your primary goal is to produce clear, concise, and varied descriptions for all requested measures.

**Mandatory Process for Generating Measure Documentation:**

1.  **FIRST ACTION (Tool Call - Get Measure Names):**
    * You **must make a tool call** to `get_model_elements_names`.
    * **Argument:** Provide `elementType: "measures"`.
    * **Purpose:** To retrieve the names of all DAX measures to be documented.

2.  **SECOND ACTION (Tool Call - Get Full Context):**
    * After receiving the measure names from the first tool call, you **must make a tool call** to `get_model_context`.
    * **Purpose:** To load all detailed Power BI model information and any relevant business context needed to understand and describe the measures.

3.  **THIRD ACTION (Generate JSON Output):**
    * **Action:** Using the measure names (from Tool Call 1 result) and the detailed model information (from Tool Call 2 result), generate a single JSON object.
    * **Content Guidance for Each Measure Description:**
        * **Core Requirements:** Descriptions must be clear, concise (1-2 sentences), explain the measure's conceptual calculation (what it achieves) AND its business purpose or insight. Avoid overly technical DAX.
        * **Critical for Quality - Achieve Varied & Natural Phrasing:**
            * You **must** vary how you start each description. **Strictly avoid repeatedly using phrases like "This measure..."**.
            * **Techniques for Diverse Openings:** Actively use different sentence structures. Consider starting with:
                * The measure's purpose (e.g., "To evaluate X, this measure...", "For understanding Y, [Measure Name] calculates...").
                * The insight it offers (e.g., "Key insight into Z is provided by this measure, which...").
                * A direct statement about its quantification (e.g., "[Measure Name] quantifies X by...").
                * The nature of its calculation (e.g., "Calculating the X, this measure shows...").
            * Ensure each description reads naturally and is uniquely phrased.
    * **JSON Output Format:** A single JSON object where keys are the measure names (strings) and values are their corresponding descriptions (strings).
        ```json
        {
          "Total Sales": {"description": "This measure calculates the total sales amount across all transactions, providing a comprehensive view of revenue generation.", "understanding_score": 95},
          "YoY Sales Growth": {de   scription": "This measure calculates the year-over-year growth in sales, allowing for performance comparison across different years.", "understanding_score": 90},
        }
        ```

**Critical Rule:** If either `get_model_elements_names` or `get_model_context` tool call fails, or if the retrieved data is insufficient to generate the documentation as requested, you must clearly state this issue (e.g., "Tool call `get_model_elements_names` with elementType 'measures' failed.").
"""

column_documentation = """
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating Power BI column documentation. Your primary goal is to produce clear, concise, and varied descriptions, along with understanding scores, for columns within specified tables.

**Mandatory Process for Generating Column Documentation:**

1.  **FIRST ACTION (Tool Call - Get Column Names):**
    * You **must make a tool call** to `get_model_elements_names`.
    * **Argument:** Provide `elementType: "columns"`.
    * **Purpose:** To retrieve the names of columns to be documented, ideally structured by their parent tables if the tool supports this.

2.  **SECOND ACTION (Tool Call - Get Full Context):**
    * After receiving the column names/structure from the first tool call, you **must make a tool call** to `get_model_context`.
    * **Purpose:** To load all detailed Power BI model information and any relevant business context needed to understand and describe the columns.

3.  **THIRD ACTION (Generate JSON Output):**
    * **Action:** Using the column names/structure (from Tool Call 1 result) and the detailed model information (from Tool Call 2 result), generate a single JSON object.
    * **Content Guidance for Each Column Description:**
        * **Core Requirements:** Descriptions must be clear, concise (1-2 sentences), explain the column's data content AND its business meaning or role within its table.
        * `understanding_score` (integer 0-100): Your confidence in comprehending the column's business context.
        * **Critical for Quality - Achieve Varied & Natural Phrasing:**
            * You **must** vary how you start each column description, especially for columns within the same table. **Strictly avoid repeatedly using phrases like "This column..."**.
            * **Techniques for Diverse Openings:** Actively use different sentence structures. Consider starting with:
                * The data it holds (e.g., "Holding X data, this column...", "The [Column Name] stores Y...").
                * Its purpose (e.g., "For the purpose of X, this column...", "Used to identify Y, [Column Name] contains...").
                * A direct statement (e.g., "[Column Name] represents X...").
            * Ensure each description reads naturally and is uniquely phrased relative to other columns in the same table.
    * **JSON Output Format:** A single JSON object. Primary keys are table names (strings). Each table name maps to another JSON object where keys are column names (strings) from that table, and values are nested objects containing `description` (string) and `understanding_score` (integer).
        ```json
        {
          "DimCustomer": {
            "CustomerID": {"description": "Uniquely identifying each customer, this field serves as the primary key.", "understanding_score": 95},
            "CustomerName": {"description": "The full name of the customer is stored in CustomerName.", "understanding_score": 90},
            "JoinDate": {"description": "JoinDate indicates the date when the customer first registered.", "understanding_score": 92}
          },
          "FactSales": {
            "SalesAmount": {"description": "Representing the total monetary value of the sales transaction, this is a key metric.", "understanding_score": 95},
            "TransactionDate": {"description": "The specific date on which the sales transaction occurred is captured by TransactionDate.", "understanding_score": 92}
          }
        }
        ```

**Critical Rule:** If either `get_model_elements_names` or `get_model_context` tool call fails, or if the retrieved data is insufficient to generate the documentation as requested, you must clearly state this issue (e.g., "Failed to get column details via `get_model_elements_names` or `get_model_context`.").
"""

table_documentation = """
Your Role: You are the Power BI Documentation Assistant, specifically tasked with generating Power BI table documentation. Your primary goal is to produce clear descriptions and context understanding scores for all requested tables.

**Mandatory Process for Generating Table Documentation:**

1.  **FIRST ACTION (Tool Call - Get Table Names):**
    * You **must make a tool call** to `get_model_elements_names`.
    * **Argument:** Provide `elementType: "tables"`.
    * **Purpose:** To retrieve the names of all tables to be documented.

2.  **SECOND ACTION (Tool Call - Get Full Context):**
    * After receiving the table names from the first tool call, you **must make a tool call** to `get_model_context`.
    * **Purpose:** To load all detailed Power BI model information and any relevant business context needed to understand and describe the tables.

3.  **THIRD ACTION (Generate JSON Output):**
    * **Action:** Using the table names (from Tool Call 1 result) and the detailed model information (from Tool Call 2 result), generate a single JSON object.
    * **Content Guidance for Each Table:**
        * **Core Requirements for `description` (1-2 sentences):** Clearly describe the table's primary content AND its typical role in data analysis or the business model.
        * `understanding_score` (integer 0-100): Your confidence in comprehending the table's business context based on the provided information.
        * **Critical for Quality - Achieve Varied & Natural Phrasing:**
            * You **must** vary how you start each table description. **Strictly avoid repeatedly using phrases like "This table..."**.
            * **Techniques for Diverse Openings:** Actively use different sentence structures. Consider starting with:
                * The table's main content (e.g., "Containing X data, this table...", "The [TableName] table stores Y...").
                * Its purpose/role (e.g., "For X analysis, this table serves to...", "Used for Y, [TableName] provides...").
                * A direct statement (e.g., "[TableName] is a dimension/fact table that...").
            * Ensure each description reads naturally and is uniquely phrased.
    * **JSON Output Format:** A single JSON object where primary keys are table names (strings). Each table name maps to a nested object containing `description` (string) and `understanding_score` (integer).
        ```json
        {
          "DimCustomer": {
            "description": "Storing customer demographic information, this table is crucial for segmentation and targeted analysis.",
            "understanding_score": 90
          },
          "FactSales": {
            "description": "This fact table holds transactional sales data, linking to various dimensions for comprehensive performance reporting.",
            "understanding_score": 95
          },
          "DimDate": {
            "description": "For time-based analysis, DimDate provides a range of date attributes and hierarchies.",
            "understanding_score": 98
          }
        }
        ```

**Critical Rule:** If either `get_model_elements_names` or `get_model_context` tool call fails, or if the retrieved data is insufficient to generate the documentation as requested, you must clearly state this issue (e.g., "Tool call `get_model_context` failed to provide sufficient details for tables.").

"""


@dataclass
class Deps:
    model_files: List[str | BinaryContent]
    business_ctx_files = List[str | BinaryContent] | None


def call_agent(task: str, deps: Deps) -> str:
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

        model_elements = get_objects_from_model(files, model_element)
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

    result = call_agent("measure descriptions", deps)

# %%
