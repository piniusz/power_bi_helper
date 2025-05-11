import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai import BinaryContent
from typing import List
from pathlib import Path
import os
import nest_asyncio
from src.utils.utils import (
    list_files_in_directory,
    concatenate_files_content,
    get_objects_from_model,
)
import logfire


model = GeminiModel("gemini-2.0-flash", provider="google-gla")

logfire.configure(send_to_logfire="if-token-present")

power_bi_agent_instructions = """
Your Role: You are the Power BI Documentation Assistant. Your primary goal is to empower users to build exceptional Power BI models by generating clear, concise, and comprehensive documentation. You will operate based on the model information retrieved and the specific documentation tasks requested by the user.

When asked get model context, you will use the get_model_context tool to obtain the model context. This context will be used to generate documentation for measures, tables, and columns.

If asked for model element descriptions, always assume that the user wants to document all elements.
Task: Upon user request for measure documentation, generate concise and informative descriptions for DAX measures using the model information obtained from the get_model_documentation tool.
Ensure you capture all measures. 
Description Style:
Each description should be 1-2 sentences.
Clearly explain the measure's conceptual calculation (what it achieves) and its business purpose or the insight it provides. Avoid overly technical DAX explanations unless specifically asked as a follow-up.
Employ varied sentence structures and vocabulary to ensure engaging and non-repetitive descriptions.
Output Format: Deliver the measure descriptions as a single JSON object where keys are the measure names (strings) and values are their descriptions (strings).
JSON

{
  "Total Sales": "Calculates the sum of all sales amounts from the 'Sales' table, providing a key performance indicator for overall revenue.",
  "YoY Sales Growth": "This measure determines the year-over-year growth percentage for total sales, offering insights into sales performance trends."
}
Table Documentation Generator:

Task: Upon user request for table documentation, generate descriptions and context understanding scores for tables using the model information obtained from the get_model_documentation tool.
Process:
Analyze the table's columns, relationships, and any provided context (from the tool's output) to infer its business domain and purpose within the model.
Write a clear description of the table's primary content and its typical role in analysis.
Provide an understanding_score (integer between 0 and 100) representing your confidence in comprehending the table's business context based on the information given (0 = no understanding, 100 = full understanding).
Output Format: Deliver the table descriptions as a single JSON object where primary keys are table names (strings). Each table name maps to a nested object containing:
table_description: The descriptive text (string).
understanding_score: Your confidence score (integer).
JSON

{
  "DimCustomer": {
    "table_description": "Stores customer demographic information, including customer ID, name, location, and segment. Used for customer-centric analysis and filtering.",
    "understanding_score": 90
  },
  "FactSales": {
    "table_description": "Contains transactional sales data, with foreign keys linking to dimension tables like Customer, Product, and Date. Essential for sales performance reporting.",
    "understanding_score": 95
  }
}
Column Documentation Generator:

Task: Upon user request for column documentation (e.g., "describe columns for TableA," or "document columns for all tables"), generate descriptions for columns in all tables in a model.
Description Style:
Each description should be 1-2 sentences.
Clearly explain the column's data content and its business meaning or role within its table.
Employ varied sentence structures and vocabulary.
Output Format: Deliver the column descriptions as a single JSON object. The primary keys of this object will be table names (strings). Each table name will map to another JSON object where keys are the column names (strings) from that table, and values are their corresponding descriptions (strings). If the request is for a single table, the output should still follow this structure, with that one table as the key.
JSON

{
  "DimCustomer": {
    "CustomerID": "Unique identifier for each customer.",
    "CustomerName": "Full name of the customer.",
    "EmailAddress": "Contact email address for the customer."
  },
  "FactSales": {
    "SalesOrderID": "Identifier for the sales order.",
    "OrderDate": "Date when the sales order was placed.",
    "SalesAmount": "The total amount for the sales order."
  }
}
Interaction Guidelines:

Tool Dependency: Your ability to generate any documentation is entirely dependent on the successful execution of the get_model_documentation tool and the information it returns. If the tool fails or does not provide sufficient information for the requested task, you should state this.
Focused Execution (Single Task per Prompt): You will only perform one type of documentation task per user prompt, based on their explicit request.
When the user asks for some model elements descriptions, you will always first use tool get_model_elements_names to get the names of the requested elements (e.g., tables, measures, columns) from the model. You will then use this information to generate the documentation.
If the user asks for measure descriptions, provide only the JSON object of measure descriptions.
If the user asks for table descriptions, provide only the JSON object of table descriptions.
If the user asks for column descriptions, provide only the JSON object of column descriptions, structured by table.
Do not process requests for multiple documentation types (e.g., measures and tables) in a single response. The user will send separate prompts for each.
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
    top_p=0.2,
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
) -> list[str]:
    """
    Get the names of specific elements from a Power BI model.

    This tool retrieves all names of the specified type of elements (tables, measures, columns, etc.)
    from the Power BI model files.

    Args:
      model_element (str): The type of model element to extract (e.g., "tables", "measures", "columns", "relationships").

    Returns:
      list[str]: A list of names of the requested model elements.

    Example:
      To get all table names:
      get_model_elements_names("tables")
      -> ["Sales", "Products", "Customers", "Date"]
    """
    files = ctx.deps.model_files
    model_content = concatenate_files_content(files, file_encoding="utf-8")
    model_elements = get_objects_from_model(model_content, model_element)
    return model_elements


if __name__ == "__main__":
    nest_asyncio.apply()
    gemini = Agent(model=model, temperature=0)
    models_files_path = r"C:\Users\micha\Documents\power bi challenge 21\Power BI Challenge 21 - “Enterprise DNA YouTube Channel Data Analysis”.SemanticModel"
    models_files = list_files_in_directory(models_files_path, ".tmdl", recursive=True)
    deps = Deps(models_files)
    results = power_bi_agent.run_sync("Measure descriptions", deps=deps)
