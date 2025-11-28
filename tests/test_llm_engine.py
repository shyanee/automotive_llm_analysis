import pytest
import os
from unittest.mock import MagicMock, patch
from google.genai import types
from google.genai.errors import APIError

# Mock data for configuration loading
TEMPERATURE=0.8
MAX_OUTPUT_TOKENS=500
MOCK_CONFIG_DATA = {
    'llm': {
        'model': 'gemini-2.5-flash',
        'temperature': TEMPERATURE,
        'max_output_tokens': MAX_OUTPUT_TOKENS
    },
    'prompts': {
        'basic_prompt': "You are a self-verifying bot.",
        'system_role': "You are a professional executive analyst."
    }
}

# --- Fixtures ---

# Fixture to mock the Gemini client and API key check
@pytest.fixture
def mock_llm_setup(mocker):
    """Mocks the os.getenv('GOOGLE_API_KEY'), genai.Client, and utils.load_config."""
    # 1. Mock the API key check
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "MOCK_API_KEY"})
    
    # 2. Mock the configuration loading
    mock_load_config = mocker.patch("src.utils.utils.load_config")
    mock_load_config.return_value = MOCK_CONFIG_DATA
    
    # 3. Mock the Gemini Client
    mock_client = mocker.patch("google.genai.Client")
    
    # Return the mock client instance for use in tests
    return mock_client.return_value

# Fixture to create an instance of LLMEngine using the mocks
@pytest.fixture
def llm_engine(mock_llm_setup):
    from src.llm_engine import LLMEngine # Import AFTER setting up mocks
    return LLMEngine()

# --- Initialization Tests ---

def test_init_raises_error_if_no_api_key(mocker):
    """Tests that initialization fails if GOOGLE_API_KEY is missing."""
    # Ensure the key is absent for this test
    mocker.patch.dict(os.environ, clear=True)
    # Re-mock load_dotenv to prevent interference from environment
    mocker.patch("dotenv.load_dotenv")
    
    from src.llm_engine import LLMEngine
    with pytest.raises(ValueError, match="GOOGLE_API_KEY not set"):
        LLMEngine()

def test_init_loads_config_correctly(llm_engine):
    """Tests that configuration parameters are loaded from the mock config file."""
    assert llm_engine.model == 'gemini-2.5-flash'
    assert llm_engine.temperature == TEMPERATURE
    assert llm_engine.max_output_tokens == MAX_OUTPUT_TOKENS
    assert "self-verifying bot" in llm_engine.basic_directives
    assert "executive analyst" in llm_engine.system_prompt
    
def test_init_uses_default_on_missing_config_keys(mocker):
    """Tests that if config file is partially missing, defaults are used."""
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "MOCK_API_KEY"})
    
    # Mock config with missing fields (e.g., temperature/tokens)
    mock_config = {'prompts': MOCK_CONFIG_DATA['prompts'], 'llm': {'model': 'gemini-2.5-pro'}}
    mocker.patch("src.utils.utils.load_config", return_value=mock_config)
    
    from src.llm_engine import LLMEngine
    engine = LLMEngine()
    
    assert engine.model == 'gemini-2.5-pro'
    assert engine.temperature == 0.6  # Default value
    assert engine.max_output_tokens == 1500 # Default value

# --- Generation Tests (generate_report_narrative) ---

def test_generate_report_success(llm_engine, mock_llm_setup):
    """Tests a successful API call returns the generated text."""
    expected_text = "## Executive Summary\nThis is the generated report."
    
    # Mock the response object
    mock_response = MagicMock()
    mock_response.text = expected_text
    
    # Set the mock client's generate_content method to return the mock response
    mock_llm_setup.models.generate_content.return_value = mock_response
    
    result = llm_engine.generate_report_narrative("Summary of data.")
    
    # Assert API was called once with the correct model
    mock_llm_setup.models.generate_content.assert_called_once()
    assert result == expected_text

def test_generate_report_handles_empty_response(llm_engine, mock_llm_setup):
    """Tests that the engine correctly handles an empty response (e.g., due to safety filter)."""
    
    # Mock response with empty text but a finish reason (e.g., safety block)
    mock_response = MagicMock()
    mock_response.text = ""
    
    # Create a mock Candidate object with a FINISH_REASON
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = types.FinishReason.SAFETY
    
    mock_response.candidates = [mock_candidate]
    
    # Set the mock client's generate_content method to return the mock response
    mock_llm_setup.models.generate_content.return_value = mock_response
    
    result = llm_engine.generate_report_narrative("Sensitive data summary.")
    
    # Check the error message contains the specific finish reason
    assert "ERROR: LLM generation returned empty text. Finish reason: SAFETY" in result

def test_generate_report_handles_api_error(llm_engine, mock_llm_setup):
    """Tests that the engine catches and reports a Gemini APIError."""
    
    # Configure the mock method to raise a specific APIError
    mock_llm_setup.models.generate_content.side_effect = APIError("Invalid API Key", response_json={})
    
    result = llm_engine.generate_report_narrative("Some data.")
    
    # Check the error message is correctly formatted
    assert "ERROR: Gemini API Call Failed. Details: Invalid API Key" in result

def test_generate_report_construction(llm_engine, mock_llm_setup):
    """Tests that the prompt construction correctly incorporates all configuration elements."""
    
    # Generation is mocked to succeed, we just check the call arguments
    mock_llm_setup.models.generate_content.return_value.text = "Mocked Text"
    
    data_summary = "Region: NA, Sales: High"
    llm_engine.generate_report_narrative(data_summary)
    
    # Get arguments used in the last call
    call_args, call_kwargs = mock_llm_setup.models.generate_content.call_args

    # content list is passed entirely via the 'contents' keyword argument.
    full_prompt_object = call_kwargs['contents']
    
    # actual full text is in the first item of that list (index 0)
    full_prompt = full_prompt_object[0]['parts'][0]['text']
    # config is also accessed via keyword arguments
    config = call_kwargs['config']
    # -------------------------
    
    # 1. Check prompt construction (Directives, Persona, Data)
    assert 'You are a self-verifying bot.' in full_prompt
    assert 'You are a professional executive analyst.' in full_prompt
    assert f'DATA CONTEXT:\n{data_summary}\n' in full_prompt
    
    # 2. Check config usage
    assert config.temperature == TEMPERATURE
    assert config.max_output_tokens == MAX_OUTPUT_TOKENS