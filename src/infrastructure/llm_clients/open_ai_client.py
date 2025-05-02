from src.infrastructure.llm_clients.base import LLMClientInterface
from openai import OpenAI

class OpenAiClient(LLMClientInterface):
    """OpenAI LLM client."""

    def __init__(self, api_key: str, **kwargs):
        """Initialize the OpenAI client."""
        self.api_key:str = api_key
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1/")
        self.model_name:str = kwargs.get("model_name", "gpt-3.5-turbo")
        self.temperature:int = kwargs.get("temperature", 1)
        self.client:OpenAI = self.get_client(api_key, **kwargs)

    def send_message(self, messages:list[dict]=None, tools:list[dict]=None, temperature:int=None):
        completion = self.client.beta.chat.completions.parse(
            messages=messages,
            model = self.model_name,
            tools=tools,
            tool_choice="auto",
            temperature = temperature
        )
        response = completion.choices[0].message
        return response
    
    def __init__(self, 
                 llm_interface:LLMClientInterface = None,
                 client_base_url:str = None,
                 model_name:str="gemini-2.0-flash", 
                 tools:list=[], 
                 system_instruction:str="",
                 temperature:int=1,
                 keep_chat_history:bool = True,
    ):
        
        self.model_name = model_name
        self.client:LLMClientInterface = llm_interface
        self.tools:list = self._get_tools_list(tools)
        self.messages:list = [
        {"role": "system", "content": system_instruction}
        ]
        self.temperature = temperature
        self.avaible_functions = {f.__name__:f for f in tools}
        self.keep_chat_history = keep_chat_history

    def __call__(self, message:str):
        log.info(f"User message: {message}")
        response = self.client.send_message(messages=self.messages, tools=self.tools, temperature=self.temperature)
        self.messages.append(response)
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
    