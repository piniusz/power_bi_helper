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
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

class Agent:
    def __init__(self, 
                 api_key:str,
                 api_url:str = None,
                 model_name:str="gemini-2.0-flash", 
                 tools:list=[], 
                 system_instruction:str="",
                 temperature:int=1,
                 keep_chat_history:bool = True,
    ):
        
        self.model_name = model_name
        self.client = self._get_client(api_key)
        self.tools:list = self._get_tools_list(tools)
        self.messages:list = [
        {"role": "system", "content": system_instruction}
        ]
        self.temperature = temperature
        self.avaible_functions = {f.__name__:f for f in tools}
        self.keep_chat_history = keep_chat_history

    def __call__(self, user_message:str):
        log.info(f"User message: {user_message}")
        response = self._send_message(user_message=user_message)
        while response.tool_calls:
            log.info(f"Tool calls: {response.tool_calls}")
            self._use_tools(response.tool_calls)
            response = self._send_message()
        self.messages.append({"role": "assistant", "content": response.content})

    def _send_message(self, user_message:str=None):
        if user_message is not None:
            self.messages.append({"role": "user", "content": user_message})
        completion = self.client.beta.chat.completions.parse(
            messages=self.messages,
            model = self.model_name,
            tools=self.tools,
            tool_choice="auto",
            temperature = self.temperature
        )
        response = completion.choices[0].message
        return response

    
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

    def _get_client(self, api_key:str, base_url:str="https://generativelanguage.googleapis.com/v1beta/openai/") ->OpenAI:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
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


# %%
