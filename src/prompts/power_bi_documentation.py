#%%
import pydantic
from google.genai import types
import re
power_bi_documentation_prompt = """
You are a Power BI documentation generator. You will be provided with a Power BI semantic model in a TMDL file.

Your task is to analyze these TMDL files to understand the structure of the Power BI model, the relationships between its objects, and the context of the measures used.

You might also receive other types of files, such as CSV, Excel, and JSON. These supplementary files will provide more comprehensive business meaning and context for the semantic model, which you should use as your primary source of understanding.

For each measure identified in the model, you will perform the following actions:

1.  **Description Generation:**
    * Create a concise description of the measure, consisting of one to two sentences. This description should explain the measure and its purpose within the model. Aim for varied phrasing and avoid consistently starting descriptions with "This measure" to maintain a natural tone.

Your output should be a JSON object adhering to the following schema:

```json
{
  "measure_renames": {
    "old_name:str": "new_name:str"
  },
  "descriptions": {
    "measure_name1:str": "measure_description1:str"
  }
}

"""
#%%


#%%
output = {
  "measure_renames": {
    r"Likes  ratio": r"Likes ratio",
    r"% by hours watched (gender)": r"% by hours watched (gender)",
    r"% by hours watched (age group)": r"% by hours watched (age group)",
    r"% by hours watched (coutries)": r"% by hours watched (countries)",
    r"Top N  Value": r"Top N value",
    r"Duration in minutes total": r"Duration in minutes total",
	r"Ideal Video vs Average": r"Ideal video vs average"
  },
  "descriptions": {
    r"% by hours watched (gender)": r"This measure calculates the sum of the 'Watch time (hours) (%)' column from the 'Viewer Gender' table. It provides the percentage of watch time broken down by gender.",
    r"% by hours watched (age group)": r"This measure calculates the sum of the 'Watch time (hours) (%)' column from the 'Viewer Age' table. It provides the percentage of watch time broken down by age group.",

  }
}


# %%
with open(r'..\..\test_data\tables\Measure table.tmdl', 'r', encoding="utf-8-sig") as file:
    file_content = file.read()
#%%
for old_name, new_name in output["measure_renames"].items():
    pattern = rf"(?:\[({old_name})\])|(?<=measure\s')({old_name})(?='\s=)|(?<=measure\s)({old_name})(?=\s=)"
    file_content_updated = re.sub(pattern, new_name, file_content)

for measure_name, measure_description in output["descriptions"].items():
    # Capture measures with description
    pattern = rf"(?<=\t///)(.*?)([\S]*?)(?=\n\tmeasure '{re.escape(measure_name)}')"
    occurrence = re.findall(pattern, file_content_updated)
    file_content_updated = re.sub(pattern, measure_description, file_content_updated)

    # Capture measures without description
    pattern = rf"(?<=\n\n\t)(measure '?{re.escape(measure_name)}'? =)"
    occurrence = re.findall(pattern, file_content_updated)
    if len(occurrence) == 1:
        replacement = f"\n\t/// {measure_description}\n\t{occurrence[0]}"
        file_content_updated = re.sub(pattern, replacement, file_content_updated)

# %%
#write the file content to a new file

# %%
