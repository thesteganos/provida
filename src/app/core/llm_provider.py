import google.generativeai as genai
import os
from app.config.settings import settings

class LLMProvider:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)

    def get_model(self, model_name: str):
        """Returns a configured Gemini model."""
        try:
            model = genai.GenerativeModel(model_name)
            return model
        except Exception as e:
            raise ValueError(f"Failed to load model {model_name}: {e}")

# Instantiate the LLMProvider globally or as needed
llm_provider = LLMProvider()
