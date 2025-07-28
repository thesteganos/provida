import logging
from typing import Any, Dict

from app.config.settings import settings
from app.core.llm_provider import llm_provider

logger = logging.getLogger(__name__)

class LanguageAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.language_agent) # Assuming a language_agent model is defined in settings

    async def detect_and_translate(self, text: str, target_language: str = "portuguese") -> Dict[str, Any]:
        """
        Detects the language of the given text and translates it to the target language if not already in it.

        Args:
            text (str): The text to detect and translate.
            target_language (str): The language to translate to (e.g., "portuguese", "english").

        Returns:
            Dict[str, Any]: A dictionary containing the detected language, translated text, and a boolean indicating if translation occurred.
        """
        prompt = f"""Detect the language of the following text. If the language is not {target_language}, translate it to {target_language}. If it is already in {target_language}, return the original text.

        Return the output in JSON format with the following keys:
        - 'detected_language': The detected language of the original text.
        - 'translated_text': The translated text if translation occurred, otherwise the original text.
        - 'translation_occurred': A boolean indicating if translation was performed.

        Text:
        {text}

        Example Output (if translation occurred):
        {{
            "detected_language": "english",
            "translated_text": "Olá, mundo!",
            "translation_occurred": true
        }}

        Example Output (if no translation occurred):
        {{
            "detected_language": "portuguese",
            "translated_text": "Olá, mundo!",
            "translation_occurred": false
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")
            result = json.loads(cleaned_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM response: {e}\nResponse: {response.text}", exc_info=True)
            return {"detected_language": "unknown", "translated_text": text, "translation_occurred": false, "error": "Invalid JSON response from model."}
        except Exception as e:
            logger.error(f"Unexpected error during language detection and translation: {e}", exc_info=True)
            return {"detected_language": "unknown", "translated_text": text, "translation_occurred": false, "error": str(e)}
