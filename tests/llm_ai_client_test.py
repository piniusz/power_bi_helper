import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv, find_dotenv
from src.infrastructure.llm_clients.open_ai_client import OpenAiClient
import os

load_dotenv(find_dotenv()) # Use the found path explicitly if needed
google_api_key = os.getenv('GOOGLE_API_KEY')
class TestOpenAiClient(unittest.TestCase):
    
    def setUp(self):
        self.api_key = google_api_key
        self.mock_client = MagicMock()
        with patch.object(OpenAiClient, 'get_client', return_value=self.mock_client):
            self.open_ai_client = OpenAiClient(self.api_key)
            self.open_ai_client.messages = []
    
    def test_send_message_calls_client_with_correct_parameters(self):
        # Arrange
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        temperature = 0.7
        
        mock_message = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=mock_message)]
        self.mock_client.beta.chat.completions.parse.return_value = mock_completion
        
        self.open_ai_client.messages = messages
        
        # Act
        self.open_ai_client.send_message(messages=messages, tools=tools, temperature=temperature)
        
        # Assert
        self.mock_client.beta.chat.completions.parse.assert_called_once_with(
            messages=messages,
            model=self.open_ai_client.model_name,
            tools=tools,
            tool_choice="auto",
            temperature=temperature
        )
        self.assertIn(mock_message, self.open_ai_client.messages)
    
    def test_send_message_appends_response_to_messages(self):
        # Arrange
        mock_message = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=mock_message)]
        self.mock_client.beta.chat.completions.parse.return_value = mock_completion
        
        initial_messages = [{"role": "user", "content": "Hello"}]
        self.open_ai_client.messages = initial_messages.copy()
        
        # Act
        self.open_ai_client.send_message()
        
        # Assert
        self.assertEqual(len(self.open_ai_client.messages), len(initial_messages) + 1)
        self.assertEqual(self.open_ai_client.messages[-1], mock_message)
    
    def test_send_message_uses_default_temperature(self):
        # Arrange
        mock_message = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=mock_message)]
        self.mock_client.beta.chat.completions.parse.return_value = mock_completion
        
        # Act
        self.open_ai_client.send_message()
        
        # Assert
        self.mock_client.beta.chat.completions.parse.assert_called_once()
        _, kwargs = self.mock_client.beta.chat.completions.parse.call_args
        self.assertEqual(kwargs.get('temperature'), None)

if __name__ == '__main__':
    unittest.main()