#%%
import base64
import inspect
from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv
import os
import inspect
import json
import logging
import requests
from io import BytesIO
from pydantic import BaseModel

load_dotenv(find_dotenv()) # Use the found path explicitly if needed
google_api_key = os.getenv('GOOGLE_API_KEY')
logging.basicConfig(level=logging.INFO)

#%%

class Agent:
    def __init__(self, 
                 api_key:str,
                 model_name:str="gemini-2.0-flash", 
                 tools:list=[], 
                 system_instruction:str="",
                 temperature:int=1,

    ):
        
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.tools = self._get_tools_list(tools)
        self.temperature = temperature
        self.system_instruction = system_instruction
        self.config = self._get_config()
        self.messages:list = []
        self.avaible_functions = {f.__name__:f for f in tools}
        self.last_assistant_message = None
        self.input_tokens = 0
        self.output_tokens = 0

    def __call__(self, user_message:str=None, keep_chat_history:bool = True, files:list = None, update_config:dict = None):
        init_config = self.config.copy()
        if update_config:
            self._update_config_dynamic(update_config)

        if not keep_chat_history:
            initial_messages = self.messages.copy()
        logging.info(f"User message: {user_message}")
        response = self._send_message(user_message=user_message, files = files)
        if response.text:
            self.last_assistant_message = response.text
            content = types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text=response.text),
                ],
            )
            self.messages.append(content)
        if response.function_calls:
            logging.info(f"Tool calls: {response.function_calls}")
            self._use_tools(response.function_calls)
            self.__call__()
        if not keep_chat_history:
            self.messages = initial_messages.copy()
            self._clean_files(files)
        self.config = init_config
        return response
    
    def print_last_assistant_message(self):
        if self.last_assistant_message:
            print(f"{self.last_assistant_message}")
        else:
            print("No assistant message available.")

    def _update_config_dynamic(self,update_dict:dict):

        for key, value in update_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logging.warning(f"Key '{key}' not found in config.")
        print(f"For this response, the config was updated to: {self.config}")

    def _upload_files(self, files:list):
        logging.info("Uploading files")
        file_parts = []
        native_extentions_supported = [".pdf", ".txt", ".xlsx"]
        other_files_mime_types = {
            ".tmdl":"text/plain"
        }
        currently_uploaded_files = {file.display_name:file for file in self.client.files.list()}
        for i in files:
            file_base_name = os.path.basename(i)
            file_extension = os.path.splitext(file_base_name)[1]
            logging.info(f"Uploading file: {os.path.basename(file_base_name)}")
            file_path = i
        
            if file_base_name in currently_uploaded_files.keys():
                logging.info(f"File {file_base_name} already uploaded. Skipping upload.")
                file = currently_uploaded_files[file_base_name]
            elif file_extension in native_extentions_supported:
                file = self.client.files.upload(
                    file=i, 
                    config={
                            "display_name":file_base_name}
                 )
            elif other_files_mime_types.get(file_extension):
                with open(file_path, "rb") as file:
                    file_bytes = file.read()
                    io_object_tmdl = BytesIO(file_bytes)
                    file = self.client.files.upload(
                        file=io_object_tmdl, 
                        config={
                                "mime_type":other_files_mime_types.get(file_extension),
                                "display_name":file_base_name}
                    )
            else:
                raise ValueError(f"Unsupported file type: {file_extension}.")
            file_parts.append(
                types.Part.from_uri(
                    file_uri=file.uri,
                    mime_type=file.mime_type,
                )
            )
        content = types.Content(
            role="user",
            parts=file_parts,
        )
        
        logging.info(f"Files uploaded: {[file.name for file in self.client.files.list()]}")
        return content

    def _clean_files(self,files_names:list[str]=None):
        logging.info("Cleaning files")
        if files_names is None:
            files_names = [file.name for file in self.client.files.list()]
        for file in self.client.files.list():
            logging.info(f"Deleting file: {file.name}")
            if file.name in files_names:
                self.client.files.delete(name=file.name)

    def _get_config(self):
        agent_config = types.GenerateContentConfig(
                            temperature = self.temperature,
                            tools = self.tools,
                            response_mime_type="text/plain",
                            system_instruction=[
                            types.Part.from_text(text=self.system_instruction)
        ],
    )
        return agent_config

    def _send_message(self, user_message:str=None, files:list = None):
        messages = self.messages.copy()
        if files:
            files = self._upload_files(files)
            messages.append(files)

        if user_message is not None:
            message = types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_message),
                ]
            )
            messages.append(message)
        response = self.client.models.generate_content(
        model="gemini-2.0-flash",
        contents=messages,
        config=self.config
    )
        self.messages.append(response)
        output_tokens = response.model_dump()['usage_metadata']['candidates_token_count']
        input_tokens = response.model_dump()['usage_metadata']['prompt_token_count']
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        logging.info(f"Input tokens: {input_tokens}")
        logging.info(f"Output tokens: {output_tokens}")
        return response

    
    def _call_function(self, name, args:dict):
        return self.avaible_functions[name](**args)
    
    def _use_tools(self,tool_calls):
        for tool_call in tool_calls:
            name = tool_call.name
            args = tool_call.args
            content = types.Content(
                role="model",
                parts=[
                    types.Part.from_function_call(
                        name=name,
                        args = args
                    )
                ]
            )
            self.messages.append(content)
            logging.info(f"Calling function: {name}")
            logging.info(f"Function arguments: {args}")
            
            result = self._call_function(name, args)
            logging.info(f"Function result: {result}")
            content = types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=name,
                        response= {"output": result},
                    )
                ]
            )
            self.messages.append(content)
    
    def _bind_tool(self,func) -> dict:
        sig = inspect.signature(func)
        type_mapping = {
                str: types.Type.STRING,
                int: types.Type.INTEGER,
                float: types.Type.NUMBER,
                bool: types.Type.BOOLEAN,
            }
        properties = {}
        required = None
        for _, param in sig.parameters.items():
            # Use annotation if available, else default to string
            arg_name = param.name
            param_type = param.annotation.__name__ 
            param_type = type_mapping.get(param.annotation)
            if param_type is None:
                exception_message = f"Unsupported type: {param.annotation}"
                raise TypeError(exception_message)
            param_type = types.Schema(type = param_type,)
            properties[arg_name] = param_type
            if param.default is inspect._empty:
                if required is None:
                    required = []
                required.append(arg_name)
        binded_tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=func.__name__,
                    description=func.__doc__,
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = required,
                        properties = properties,
                    ),
                ),
            ])

        return binded_tool
    
    def _get_tools_list(self,unbinded_tools):
        tools = []
        for tool in unbinded_tools:
            binded_tool = self._bind_tool(tool)
            tools.append(binded_tool)
        return tools
    



# def addition(no_1:float, no_2:float):
#     """
#     Add two numbers together.

#     Args:
#         no_1 (float): The first number to add.
#         no_2 (float): The second number to add.

#     Returns:
#         float: The sum of no_1 and no_2.
#     """
#     return no_1+no_2


# #%%
# system_instruction = """
# You are a calculator that can add 2 numbers together.
# You do claculation by using tools.
#     """
# chat = Agent(
#     api_key=google_api_key,
#     model_name="gemini-2.0-flash",
#     system_instruction=system_instruction,
#     tools=[addition, ],
#     temperature=0.2,
# )
# %%

# #get relative path of the file C:\Users\micha\Documents\Agents\travel_agent\test_data\Measure table.tmdl when current dir is 'c:\\Users\\micha\\Documents\\Agents\\travel_agent\\src\\agents'
# files = []
# for file in os.listdir(r"..\..\test_data\tables"):
#     if os.path.isfile(os.path.join(r"..\..\test_data\tables", file)):
#         files.append(os.path.join(r"..\..\test_data\tables", file))
#         print(os.path.join(r"..\..\test_data\tables", file))
# chat(
#     user_message="Can you brief me about this semantic model?", 
#     files=files, 
#     keep_chat_history=True)

