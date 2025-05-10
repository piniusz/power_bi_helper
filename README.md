# Power BI Doctor (Helper)

An AI-powered assistant for documenting and managing Power BI models.

## Overview

Power BI Doctor is a tool designed to help Power BI developers document their semantic models efficiently. It leverages AI to automatically generate clear and comprehensive documentation for measures, tables, and columns within your Power BI models.

## Features

- **Measure Documentation**: Automatically generate concise and informative descriptions for DAX measures
- **Table Documentation**: Create descriptions for tables with confidence scores on context understanding
- **Column Documentation**: Generate clear descriptions for columns across all tables
- **TMDL File Support**: Works with the TMDL (Tabular Model Definition Language) file format used by Power BI
- **Batch Processing**: Process multiple files at once to document entire models

## Requirements

- Python 3.11 or newer
- Google AI API key (for Gemini model access)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/power_bi_doctor.git

# Navigate to the project directory
cd power_bi_doctor/power_bi_helper

# Install dependencies
pip install -e .
```

## Configuration

1. Create a `.env` file in the project root with your API key:

```
GEMINI_API_KEY=your_api_key_here
IS_LOCAL=1
```

## Usage

### Command Line Interface

```python
# Example: Generate documentation for a Power BI model
python power_bi_doctor.py
```

### Library Usage

```python
import asyncio
from src.utils.utils import list_files_in_directory
from src.agents.powerBI_documenter_agent import power_bi_agent, Deps

# Path to your Power BI model files
model_files_path = "path/to/your/model/files"
model_files = list_files_in_directory(model_files_path, ".tmdl", recursive=True)

# Create dependencies
deps = Deps(model_files)

# Get measure descriptions
result = power_bi_agent.run_sync("Measure descriptions", deps=deps)
print(result.output)

# Get table descriptions
result = power_bi_agent.run_sync("Table descriptions", deps=deps)
print(result.output)

# Get column descriptions
result = power_bi_agent.run_sync("Column descriptions", deps=deps)
print(result.output)
```

## Project Structure

- `src/agents/`: Contains the AI agent implementations
- `src/utils/`: Utility functions for file handling and other operations
- `src/infrastructure/`: LLM client implementations
- `tests/`: Test cases and fixtures

## License

[MIT License](LICENSE)

