from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class LLMClientInterface(ABC):
    """Interface for LLM clients.

    This interface defines the methods that any LLM client must implement.
    It allows for different LLM clients to be used interchangeably in the codebase.
    """

    @abstractmethod
    def send_message(self,
                     messages: List[Dict[str, Any]],
                     tools: List[Dict[str, Any]],
                     temperature: Optional[float] = 1,
                     **kwargs) -> Dict[str, Any]:
        """Send a message to the LLM and return the response."""
        pass
    def get_client(api_key: str, **kwargs) -> Any:
        """Get the LLM client instance."""
        pass
    

    def get_tools_list(self,tools:List[callable]) -> List[Dict[str, Any]]:
        """Get the tools list."""
        pass