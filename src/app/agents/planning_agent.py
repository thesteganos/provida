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
        prompt = f"""Você é um Agente de Planejamento de Pesquisa. Sua tarefa é criar um plano de pesquisa detalhado para o tópico fornecido e estimar os recursos necessários (número de buscas, chamadas de API). O plano deve ser estruturado em etapas claras, com sub-perguntas ou sub-tópicos para cada etapa.

        Tópico da Pesquisa: {topic}

        Formato de Saída (JSON):
        {{
            "plan": [
                {{
                    "step": "Nome da Etapa",
                    "description": "Descrição detalhada da etapa",
                    "sub_questions": [
                        "Sub-pergunta 1",
                        "Sub-pergunta 2"
                    ]
                }}
            ],
            "estimated_resources": {{
                "num_searches": "Número estimado de buscas na web",
                "num_api_calls": "Número estimado de chamadas de API (LLM)",
                "estimated_time_minutes": "Tempo estimado em minutos para completar a pesquisa"
            }}
        }}

        Certifique-se de que a saída seja um JSON válido e completo.
        """

        try:
            response = await self.model.generate_content_async(prompt)
            cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")
            plan_data = json.loads(cleaned_text)
            return plan_data
        except Exception as e:
            logger.error(f"Erro ao gerar plano de pesquisa: {e}", exc_info=True)
            return {"error": str(e), "plan": [], "estimated_resources": {}}
