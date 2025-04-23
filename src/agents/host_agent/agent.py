#%%
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os

# %%

load_dotenv(find_dotenv()) # Use the found path explicitly if needed
google_api_key = os.getenv('GOOGLE_API_KEY')
# %%
client = OpenAI(
    api_key=google_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
# %%
