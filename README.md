# Power BI Doctor (Helper)

An AI-powered assistant for documenting and managing Power BI models.

## Overview

Power BI Doctor is a Python-based tool designed to help Power BI developers and data analysts efficiently document their semantic models. It leverages Large Language Models (LLMs), primarily Google's Gemini, to automatically generate clear and comprehensive documentation for measures, tables, and columns within your Power BI models defined using TMDL (Tabular Model Definition Language).

The tool processes TMDL files, interacts with an AI agent to understand the model elements, and then generates descriptions. It can update your TMDL files directly or create an updated copy with the new documentation.

## Features

-   **Automated Measure Documentation**: Generates concise and informative descriptions for DAX measures, explaining their calculation and business purpose.
-   **Automated Table Documentation**: Creates descriptions for tables, outlining their content and role in the data model.
-   **Automated Column Documentation**: Produces clear descriptions for columns, detailing their data and business meaning.
-   **TMDL File Processing**: Works directly with `.tmdl` files, the standard format for Power BI semantic models.
-   **AI-Powered**: Utilizes Google Gemini models via the `pydantic-ai` library and a custom Google AI client for intelligent documentation generation.
-   **Context-Aware Descriptions**: Can leverage business context files (e.g., glossaries, data dictionaries) to improve documentation quality.
-   **Batch Processing**: Processes all TMDL files within a specified model directory.
-   **Output Options**: Creates a new folder with updated TMDL files, preserving your original model.

## Requirements

-   Python 3.11 or newer
-   A Google API Key with access to Gemini models.
-   Poetry for dependency management (recommended).

Key Python libraries:
-   `pydantic-ai`
-   `google-generativeai`
-   `python-dotenv`
-   `pytest` (for development/testing)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd power_bi_helper
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```
    Alternatively, if not using Poetry, you might be able to install with pip, but `pyproject.toml` is set up for Poetry:
    ```bash
    # Ensure pip is up to date and install build
    # python -m pip install --upgrade pip build
    # python -m pip install -e .
    ```

## Configuration

1.  **Create a `.env` file** in the `power_bi_helper` project root directory.
2.  **Add your Google API Key** to the `.env` file:
    ```env
    GOOGLE_API_KEY="your_google_api_key_here"
    ```
    This key is used by the agents to interact with the Google Gemini LLM.

## Usage

### Command Line Interface (Main Script)

The primary way to use the Power BI Doctor is through the `power_bi_doctor.py` script.

1.  **Ensure your `.env` file is configured** with the `GOOGLE_API_KEY`.
2.  **Modify the `files_path` variable** in `power_bi_doctor.py` to point to your Power BI Semantic Model folder (the one containing the `.tmdl` files).
    ```python
    # filepath: power_bi_doctor.py
    # ...
    if __name__ == "__main__":
        # ...
        files_path = r"C:\path\to\your\Competitive Marketing Analysis.SemanticModel" # UPDATE THIS PATH
        # ...
    ```
3.  **Run the script:**
    ```bash
    python power_bi_doctor.py
    ```

The script will:
-   List all `.tmdl` files in the specified directory.
-   Call the AI agent to generate documentation for measures, tables, and columns.
-   Create a new folder named `<YourSemanticModelFolder>_updated` (e.g., `Competitive Marketing Analysis.SemanticModel_updated`) in the same parent directory as your original model.
-   Populate this new folder with copies of your original `.tmdl` files, updated with the generated descriptions.

### Library Usage

You can also use the core agent functionality as a library in your own Python scripts.

```python
# filepath: your_custom_script.py
import asyncio
import os
from src.utils.utils import list_files_in_directory
from src.agents.powerBI_documenter_agent import call_agent, Deps, ObjectDetailsList

# If running in an environment like a script where an event loop isn't already running,
# and you encounter issues with asyncio, you might need nest_asyncio.
# import nest_asyncio
# nest_asyncio.apply()

async def generate_docs():
    # Path to your Power BI model files
    model_files_path = r"C:\path\to\your\Competitive Marketing Analysis.SemanticModel" # UPDATE THIS
    if not os.path.exists(model_files_path):
        print(f"Error: Model path not found: {model_files_path}")
        return

    model_files = list_files_in_directory(model_files_path, ".tmdl", recursive=True)
    if not model_files:
        print(f"No .tmdl files found in {model_files_path}")
        return

    # Business context files (optional)
    # business_ctx_files_path = "path/to/your/business/context/files"
    # business_files = []
    # if business_ctx_files_path and os.path.exists(business_ctx_files_path):
    #     business_files = list_files_in_directory(business_ctx_files_path, recursive=True)
    # deps = Deps(model_files=model_files, business_ctx_files=business_files if business_files else None)
    
    deps = Deps(model_files=model_files)

    # Available tasks: "measure descriptions", "column descriptions", "table descriptions"
    tasks = ["measure descriptions", "table descriptions", "column descriptions"]
    
    all_documentation = {}

    for task in tasks:
        print(f"Requesting: {task}...")
        # The call_agent function is async
        # It returns a tuple: (output_object, model_files_list)
        # The first element (output_object) is an instance of ObjectDetailsList or similar Pydantic model
        result_data, _ = await call_agent(task=task, deps=deps)
        
        if result_data and isinstance(result_data, ObjectDetailsList) and result_data.objects_documentation:
            print(f"Received documentation for {task}:")
            all_documentation[task] = []
            for doc_item in result_data.objects_documentation:
                print(f"  Type: {doc_item.type}, Name: {doc_item.name}, Source: {doc_item.source_table}")
                print(f"  Description: {doc_item.description}")
                print(f"  Confidence: {doc_item.confidence}\n")
                all_documentation[task].append(doc_item)
        else:
            print(f"No documentation generated or an issue occurred for {task}.")
            if result_data:
                 print(f"Received data: {result_data}")


if __name__ == "__main__":
    # Ensure GOOGLE_API_KEY is set in your environment or .env file
    # from dotenv import load_dotenv
    # load_dotenv()
    # if not os.getenv("GOOGLE_API_KEY"):
    #     print("Error: GOOGLE_API_KEY not found in environment. Please set it in .env file.")
    # else:
    #     asyncio.run(generate_docs())
    pass # Placeholder for actual execution logic if you adapt this example
```

## Project Structure

-   `power_bi_doctor.py`: Main executable script for generating documentation.
-   `src/`: Source code directory.
    -   `agents/`: Contains AI agent implementations.
        -   `powerBI_documenter_agent.py`: Core agent logic using `pydantic-ai` for generating documentation for measures, columns, and tables.
        -   `agent_google.py`: A custom agent implementation for interacting with Google's Generative AI.
        -   `agent.py`: A more generic agent structure (potentially for OpenAI or other compatible APIs).
    -   `infrastructure/`: LLM client implementations and base classes.
        -   `llm_clients/`: Specific client implementations (e.g., `open_ai_client.py`, `base.py`).
    -   `prompts/`: (Currently empty) Intended for storing detailed LLM prompts if separated from agent code.
    -   `tools/`: (Currently empty) Intended for custom tools that agents can use.
    -   `utils/utils.py`: Utility functions for file handling (listing files, reading TMDL), text processing (updating descriptions in TMDL content), and extracting model objects.
-   `tests/`: Contains test cases and fixtures for ensuring code quality and correctness.
    -   `fixtures/`: Sample TMDL files and test data.
-   `pyproject.toml`: Project metadata and dependencies definition for Poetry.
-   `poetry.lock`: Exact versions of dependencies.
-   `.env`: (To be created by user) For storing API keys and environment variables.
-   `README.md`: This file.

## How it Works

1.  **File Discovery**: The `power_bi_doctor.py` script (or your custom script) uses `list_files_in_directory` from `src.utils.utils` to find all `.tmdl` files in the specified Power BI model path.
2.  **Agent Invocation**: For each documentation task (measures, columns, tables), the `call_agent` function in `src.agents.powerBI_documenter_agent.py` is invoked.
3.  **AI Agent Processing**:
    *   The `powerBI_documenter_agent` is a `pydantic-ai` agent configured with a Google Gemini model.
    *   It follows a system prompt tailored to the specific task (e.g., `measure_documentation` prompt).
    *   **Tool Usage**: The agent uses built-in tools:
        *   `get_model_elements_names`: Calls `get_objects_from_model` (from `src.utils.utils`) to extract names of measures, columns, or tables from the TMDL files.
        *   `get_model_context`: Loads the content of TMDL files (and optionally business context files) as `BinaryContent` for the LLM.
    *   **Description Generation**: The LLM generates descriptions based on the prompts, the extracted names, and the provided model/business context. The output is structured according to Pydantic models like `ObjectDetailsList`.
4.  **Result Processing**: The `process_documentation_results` function in `power_bi_doctor.py` organizes the structured output from the agent into a dictionary.
5.  **TMDL Update**:
    *   A new directory (e.g., `model_updated`) is created.
    *   The original TMDL files are copied to this new directory.
    *   The `update_measures_columns_descriptions` and `update_table_description` functions (from `src.utils.utils`) are used to insert the generated descriptions into the TMDL content of the files in the `_updated` directory.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs, feature requests, or improvements.

(Consider adding more specific contribution guidelines if the project grows, e.g., coding standards, test requirements.)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (if one exists, otherwise state "MIT License").