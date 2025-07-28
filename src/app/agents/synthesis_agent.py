import json
import logging

from app.core.llm_provider import llm_provider
from app.config.settings import settings
from app.models.research_models import FinalReport
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SynthesisAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.synthesis_agent)

    async def generate_summary_with_citations(self, text: str, research_question: str, sources: List[Dict[str, str]]) -> FinalReport:
        """Generates a summary with sentence-level citations.

        Args:
            text (str): The text to summarize.
            research_question (str): The research question the summary should address.
            sources (List[Dict[str, str]]): A list of dictionaries, each containing 'id' and 'content' of the source.

        Returns:
            Dict[str, Any]: A dictionary containing the summary and extracted citations.
        """
        # Format sources for the prompt
        formatted_sources = ""
        for source in sources:
            formatted_sources += f"ID: {source['id']}\nContent: {source['content']}\n\n"

        from app.prompts.llm_prompts import SYNTHESIS_AGENT_PROMPT

        prompt = SYNTHESIS_AGENT_PROMPT.format(
            text=text,
            formatted_sources=formatted_sources,
            research_question=research_question
        )

        try:
            response = await self.model.generate_content_async(prompt)
            summary_data = FinalReport(**json.loads(response.text))
            return summary_data
        except Exception as e:
            print(f"Error generating summary: {e}")
            return FinalReport(summary="", citations_used=[])