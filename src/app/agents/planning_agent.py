import json
import logging

from app.core.llm_provider import llm_provider
from app.config.settings import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PlanningAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.planning_agent)

    async def generate_research_plan(self, topic: str) -> Dict[str, Any]:
        """Generates a detailed research plan and estimates resources.

        Args:
            topic (str): The research topic.
        Returns:
            Dict[str, Any]: A dictionary containing the research plan and estimated resources.
        """
        from app.prompts.llm_prompts import PLANNING_AGENT_PROMPT

        prompt = PLANNING_AGENT_PROMPT.format(topic=topic)

        try:
            response = await self.model.generate_content_async(prompt)
            cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")
            plan_data = json.loads(cleaned_text)
            return plan_data
        except Exception as e:
            logger.error(f"Erro ao gerar plano de pesquisa: {e}", exc_info=True)
            return {"error": str(e), "plan": [], "estimated_resources": {}}
