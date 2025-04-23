#%%
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
import inspect
import json
import logging

# %%

load_dotenv(find_dotenv()) # Use the found path explicitly if needed
google_api_key = os.getenv('GOOGLE_API_KEY')
log = logging.getLogger()
log.setLevel(logging.INFO)
# Add handler to display logs in console
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
# %%
client = OpenAI(
    api_key=google_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)
# %%

class Agent:
    def __init__(self, 
                 model_name="gemini-2.0-flash", 
                 tools:list=[], 
                 system_instruction:str="",
                 temperature:int=1,
                 keep_chat_history:bool = True):
        
        self.model_name = model_name
        self.client:OpenAI = self._get_client()
        self.tools:list = self._get_tools_list(tools)
        self.messages:list = [
        {"role": "system", "content": system_instruction}
        ]
        self.temperature = temperature
        self.avaible_functions = {f.__name__:f for f in tools}
        self.keep_chat_history = keep_chat_history

    def __call__(self, message:str):
        log.info(f"User message: {message}")
        self._send_message(message)
        while self.messages[-1].tool_calls:
            log.info(f"Tool calls: {self.messages[-1].tool_calls}")
            self._use_tools(self.messages[-1].tool_calls)
            self._send_message()
        if self.messages[-1].content:
            print(self.messages[-1].content)
        if not self.keep_chat_history:
            self.messages = self.messages[0]


    
    def _call_function(self, name, args:dict):
        return self.avaible_functions[name](**args)
    
    def _use_tools(self,tool_calls):
        for tool_call in tool_calls:
            name = tool_call.function.name
            log.info(f"Calling function: {name}")
            log.info(f"Function arguments: {tool_call.function.arguments}")
            args = json.loads(tool_call.function.arguments)
            result = self._call_function(name, args)
            self.messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
    )

    def _send_message(self, user_input:str=None):
        if user_input:
            self.messages.append({"role":"user", "content":user_input})
        completion = client.beta.chat.completions.parse(
            messages=self.messages,
            model = self.model_name,
            tools=self.tools,
            tool_choice="auto",
            temperature = self.temperature
        )
        self.messages.append(completion.choices[0].message)

    def _get_client(self, ) ->OpenAI:
        client = OpenAI(
            api_key=google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        return client
    def _bind_tool(self,func) -> dict:
        sig = inspect.signature(func)
        required = []
        type_mapping = {
                str: "string",
                int: "number",
                float: "float",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
        properties={}
        for _, param in sig.parameters.items():
            # Use annotation if available, else default to string
            arg_name = param.name
            param_type = param.annotation.__name__ 
            param_type = type_mapping.get(param.annotation)
            if param_type is None:
                exception_message = f"Unsupported type: {param.annotation}"
                raise TypeError(exception_message)
            param_type = {"type":param_type}
            properties[arg_name] = param_type
            if param.default is inspect._empty:
                required.append(arg_name)
        tool_dict = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False
            },
            "strict": True
        }
    }
        return tool_dict
    
    def _get_tools_list(self,unbinded_tools):
        tools = []
        for tool in unbinded_tools:
            binded_tool = self._bind_tool(tool)
            tools.append(binded_tool)
        return tools
    



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
prompt = """
    You are a simple calculator. You know how to add 2 integers  and how to multiply 2 integers. 
    For this you will always use your avaible tools: addition and multiplication.
    Knowing that you decide whether you can answer user question using your tool, if you can't you politely appoligize and say you can't answer that question
"""
tools = [addition, multiplication]
chat = Agent(system_instruction=prompt, tools=tools, temperature=0.3)
chat("What would be a result if I would first add 5 and 9, then add to it 30 then wanted to multiply it by result of 9 and 3?")
# %%



# %%
