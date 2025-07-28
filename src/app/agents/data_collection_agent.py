import asyncio
import logging
from typing import List, Dict, Any, Coroutine

from app.models.research_models import CollectedDataItem
from app.tools.brave_search import BraveSearchTool
from app.tools.pubmed_search import PubMedSearchTool
from app.agents.routing_agent import RoutingAgent

logger = logging.getLogger(__name__)

class DataCollectionAgent:
    """
    Agente responsável por coletar dados de fontes externas de forma dinâmica,
    utilizando um agente de roteamento para selecionar a melhor ferramenta.
    """

    def __init__(self):
        # Mapeamento de nomes de ferramentas para suas instâncias
        self.tools = {
            "brave_search": BraveSearchTool(),
            "pubmed_search": PubMedSearchTool(),
        }
        # Descrições das ferramentas para o RoutingAgent
        tool_descriptions = [
            {"name": "brave_search", "description": "Uma ferramenta de busca geral para responder a uma ampla variedade de perguntas. Use para notícias, eventos atuais, informações gerais, etc."},
            {"name": "pubmed_search", "description": "Uma ferramenta de busca especializada para encontrar pesquisas biomédicas e artigos científicos no campo da medicina e ciências da vida. Use para perguntas sobre condições médicas, tratamentos, biologia, etc."},
        ]
        self.routing_agent = RoutingAgent(tools=tool_descriptions)

    async def collect_data(self, research_plan: Dict[str, Any]) -> List[CollectedDataItem]:
        """
        Executa o plano de pesquisa, roteia cada consulta para a ferramenta apropriada,
        coleta os dados e os retorna.

        Args:
            research_plan (Dict[str, Any]): O plano de pesquisa gerado pelo PlanningAgent.

        Returns:
            List[CollectedDataItem]: Uma lista de itens de dados coletados.
        """
        if not research_plan or "research_questions" not in research_plan:
            logger.warning("Plano de pesquisa inválido ou vazio. Nenhum dado será coletado.")
            return []

        # Cria uma tarefa de busca para cada pergunta no plano
        tasks: List[Coroutine] = [
            self._route_and_search(question["query"])
            for question in research_plan["research_questions"]
        ]

        search_results_list = await asyncio.gather(*tasks)

        # Achatando a lista de listas de resultados
        flat_results = [item for sublist in search_results_list for item in sublist]

        # Converte os resultados brutos para o formato CollectedDataItem
        collected_data = [
            CollectedDataItem(
                source_identifier=result.get("url") or result.get("title", "N/A"),
                content=result.get("content") or result.get("snippet", ""),
            )
            for result in flat_results
        ]

        logger.info(f"{len(collected_data)} itens de dados coletados de {len(tasks)} consultas.")
        return collected_data

    async def _route_and_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Roteia uma consulta para a melhor ferramenta e executa a busca.
        """
        try:
            tool_name = await self.routing_agent.choose_tool(query)

            # Seleciona a ferramenta do dicionário; usa brave_search como fallback.
            tool_to_use = self.tools.get(tool_name, self.tools["brave_search"])

            if tool_name not in self.tools:
                logger.warning(f"Ferramenta '{tool_name}' não encontrada. Usando 'brave_search' como fallback.")

            logger.info(f"Usando a ferramenta '{tool_to_use.__class__.__name__}' para a consulta: '{query}'")
            return await tool_to_use.run(query)
        except Exception as e:
            logger.error(f"Erro ao rotear ou executar a busca para a consulta '{query}': {e}", exc_info=True)
            return []
