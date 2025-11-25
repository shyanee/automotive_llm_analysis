import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError # Import for specific error handling

from src.utils import utils

class LLMEngine:
    """
    Replaces LocalLLMEngine with Google Gemini API backend.
    Generates reports using the cloud-based Gemini model.
    """

    def __init__(self, config_path="config/llm_config.yml", model="gemini-2.5-flash"):
        """
        Initializes the Gemini client.
        Expects environment variable GOOGLE_API_KEY to be set.
        """
        load_dotenv()  # Reads .env automatically
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set or is empty.")

        # Initialize client and configurations
        self.client = genai.Client(api_key=api_key)
        self.llm_config = utils.load_config(config_path)
        llm_settings = self.llm_config.get('llm', {})
        
        # Load model configuration
        self.model = llm_settings.get('model', model)
        self.temperature = llm_settings.get('temperature', 0.5)
        self.max_output_tokens = llm_settings.get('max_output_tokens', 2000)
        # Load prompt templates
        self.basic_directives = self.llm_config['prompts']['basic_prompt']
        self.system_prompt = self.llm_config['prompts']['system_role']
        
        print(f"LLM initialized with model: {self.model}\nTemp: {self.temperature}\nMax Tokens: {self.max_output_tokens}\n")

    def generate_report_narrative(self, data_summary: str) -> str:
        # Construct the final user prompt, combining Basic Directives (Guardrails) and System Role (Persona/Structure)
        full_instruction = (
            f"{self.basic_directives}\n\n" # Quality Guardrails (e.g., Self-Verification, Challenging Assertions)
            "--- END OF ANALYTICAL DIRECTIVES ---\n\n"
            
            f"**Analyst Role & Required Report Structure:** {self.system_prompt}\n\n" # Persona/Structure
            
            "Your report generation task starts now. Generate a complete, professional executive report "
            "in Markdown format. Use the provided data summary and reference the generated visualizations "
            "to support your analysis, following the required structural sections.\n\n"
            
            f"DATA CONTEXT:\n{data_summary}\n"
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    {"role": "user", "parts": [{"text": full_instruction}]}
                ],
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens
                )
            )
            
            # Check if the text is available and non-empty
            if response.text:
                return response.text
            else:
                # Handle cases where the response is empty (e.g., safety block)
                if response.candidates and response.candidates[0].finish_reason:
                    return f"ERROR: LLM generation returned empty text. Finish reason: {response.candidates[0].finish_reason.name}"
                return "ERROR: LLM generation returned an empty or unparsable response."

        except APIError as e:
            # Catch specific Gemini API errors (e.g., resource exhausted, invalid key)
            return f"ERROR: Gemini API Call Failed. Details: {e}"
        except Exception as e:
            # Catch other potential errors (e.g., network issues)
            return f"ERROR: An unexpected error occurred during LLM generation. Details: {e}"