from src.agents.agent import Agent
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv()) # Use the found path explicitly if needed
google_api_key = os.getenv('GOOGLE_API_KEY')

system_prompt = """
You are an calculator. You can only do calculations. You can do addition and multiplication.
For this task you are using tools:
1.addition
2.multiplication
When user gives you a task, you will first check if it is a calculation task or not.
If it is a calculation task, you will use the tools to do the calculation. If it is not a calculation task, you will say "I can only do calculations".
"""
def addition(no_1:int, no_2:int):
    """
    Adds two integer numbers together.

    Args:
        no_1 (int): The first number to add.
        no_2 (int): The second number to add.

    Returns:
        int: The sum of the two input numbers.
    """
    return no_1+no_2
def multiplication(no:int, no2:int):
    """
    Multiply two numbers together.
    
    Args:
        no (int or float): The first number.
        no2 (int or float): The second number.
        
    Returns:
        int or float: The product of the two numbers.
    """
    return no*no2
tools = [addition, multiplication]
chat_bot = Agent(
    api_key=google_api_key,
    model_name="gemini-2.0-flash",
    system_instruction=system_prompt,
    tools=tools,
    temperature=0.2,
    keep_chat_history=True
)

chat_bot("What is 2+2?")