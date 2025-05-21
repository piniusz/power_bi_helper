import pytest
import src.agents.agent_google as agent_google

def sample_function_1(arg1:int, arg2:int):
    """Sample function 1 for testing."""
    return arg1 + arg2

def sample_function_2(arg1:int, arg2:int):
    """Sample function 2 for testing."""
    return arg1 * arg2


def test_agent_initialization(mocker):
    """Test the initialization of the Google AI agent."""
    
    agent = agent_google.Agent(
        api_key= "your_google_api_key",
        model_name="test_model",
        tools=[sample_function_1, sample_function_2],
        system_instruction="Test system instruction",
        temperature=1
    )
    assert agent.model_name == "test_model"
    assert agent.temperature == 1  
    assert len(agent.tools) == 2
    assert agent.system_instruction == "Test system instruction"
    assert agent.temperature == 1
    assert [name for name, _ in agent.avaible_functions.items()] == ["sample_function_1", "sample_function_2"]