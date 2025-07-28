import asyncio
import logging
from typing import List, Dict, Any

from app.models.research_models import CollectedDataItem
from app.tools.brave_search import BraveSearchTool
from app.tools.pubmed_search import PubMedSearchTool

logger = logging.getLogger(__name__)

class DataCollectionAgent:
    """
    Agente responsável por coletar dados de fontes externas com base em um plano de pesquisa.
    """

    def __init__(self):
        self.brave_search = BraveSearchTool()
        self.pubmed_search = PubMedSearchTool()

    async def collect_data(self, research_plan: Dict[str, Any]) -> List[CollectedDataItem]:
        """
        Executa o plano de pesquisa, coleta dados e os retorna.

        Args:
            research_plan (Dict[str, Any]): O plano de pesquisa gerado pelo PlanningAgent.

        Returns:
            List[CollectedDataItem]: Uma lista de itens de dados coletados.
        """
        if not research_plan or "research_questions" not in research_plan:
            logger.warning("Plano de pesquisa inválido ou vazio. Nenhum dado será coletado.")
            return []

        tasks = []
        for question in research_plan["research_questions"]:
            query = question["query"]
            # Para simplificar, vamos usar a busca geral (Brave) para todas as questões.
            # Em uma implementação mais avançada, poderíamos usar um classificador
            # para escolher a melhor ferramenta (Brave, PubMed, etc.) para cada questão.
            tasks.append(self._search_with_tool(self.brave_search, query))

        # Adiciona uma busca específica no PubMed se houver uma questão acadêmica
        if "academic_questions" in research_plan:
            for question in research_plan["academic_questions"]:
                query = question["query"]
                tasks.append(self._search_with_tool(self.pubmed_search, query))

        search_results = await asyncio.gather(*tasks)

        # Achatando a lista de listas de resultados
        flat_results = [item for sublist in search_results for item in sublist]

        # Converte os resultados para o formato CollectedDataItem
        collected_data = []
        for result in flat_results:
            collected_data.append(
                CollectedDataItem(
                    source_identifier=result.get("url") or result.get("title"),
                    content=result.get("content") or result.get("snippet"),
                )
            )

        logger.info(f"{len(collected_data)} itens de dados coletados.")
        return collected_data

    async def _search_with_tool(self, tool, query: str) -> List[Dict[str, Any]]:
        """
        Executa uma busca com a ferramenta especificada e trata os erros.
        """
        try:
            return await tool.run(query)
        except Exception as e:
            logger.error(f"Erro ao executar a busca com a ferramenta {tool.__class__.__name__} para a consulta '{query}': {e}", exc_info=True)
            return []
