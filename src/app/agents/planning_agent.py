import logging
from typing import Dict, Any

from app.core.llm_provider import llm_provider
from app.config.settings import settings
from app.agents.utils import extract_json_from_response

logger = logging.getLogger(__name__)

class PlanningAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.planning_agent)

    async def generate_research_plan(self, topic: str) -> Dict[str, Any]:
        """Gera um plano de pesquisa detalhado e estima os recursos.

        Args:
            topic (str): O tópico da pesquisa.
        Returns:
            Dict[str, Any]: Um dicionário contendo o plano de pesquisa e os recursos estimados.
        """
        from app.prompts.llm_prompts import PLANNING_AGENT_PROMPT

        prompt = PLANNING_AGENT_PROMPT.format(topic=topic)

        try:
            response = await self.model.generate_content_async(prompt)
            plan_data = extract_json_from_response(response.text)
            return plan_data
        except (ValueError, Exception) as e:
            logger.error(f"Erro ao gerar plano de pesquisa: {e}", exc_info=True)
            return {"error": str(e), "plan": [], "estimated_resources": {}}
