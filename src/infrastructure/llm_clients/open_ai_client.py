from base import LLMClientInterface
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
            messages=self.messages,
            model = self.model_name,
            tools=tools,
            tool_choice="auto",
            temperature = temperature
        )
        self.messages.append(completion.choices[0].message)