import logging
from typing import List, Dict, Any

from app.core.llm_provider import llm_provider
from app.config.settings import settings
from app.prompts.llm_prompts import ROUTING_AGENT_PROMPT

logger = logging.getLogger(__name__)

class RoutingAgent:
    def __init__(self, tools: List[Dict[str, Any]]):
        """
        Inicializa o RoutingAgent.

        Args:
            tools (List[Dict[str, Any]]): Uma lista de dicionários, onde cada dicionário
                                          descreve uma ferramenta (nome e descrição).
        """
        self.model = llm_provider.get_model(settings.models.routing_agent)
        self.tools_description = self._format_tools_for_prompt(tools)

    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """Formata a lista de ferramentas em uma string para o prompt."""
        description = ""
        for tool in tools:
            description += f"- Ferramenta: `{tool['name']}` - Descrição: {tool['description']}\n"
        return description

    async def choose_tool(self, query: str) -> str:
        """
        Escolhe a melhor ferramenta para uma determinada consulta.

        Args:
            query (str): A consulta ou pergunta de pesquisa.

        Returns:
            str: O nome da ferramenta escolhida.
        """
        prompt = ROUTING_AGENT_PROMPT.format(
            tools_description=self.tools_description,
            query=query
        )

        try:
            response = await self.model.generate_content_async(prompt)
            # A resposta do LLM deve ser apenas o nome da ferramenta.
            # O strip() remove espaços em branco ou novas linhas extras.
            tool_name = response.text.strip()
            logger.info(f"Consulta: '{query[:50]}...' -> Ferramenta escolhida: {tool_name}")
            return tool_name
        except Exception as e:
            logger.error(f"Erro ao escolher a ferramenta para a consulta '{query}': {e}", exc_info=True)
            # Fallback para uma ferramenta padrão em caso de erro.
            return "default_search"
