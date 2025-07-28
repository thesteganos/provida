import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime 

from app.config.settings import settings
from app.core.llm_provider import llm_provider
from app.agents.memory_agent import MemoryAgent
from app.agents.knowledge_graph_agent import KnowledgeGraphAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.research_agent import ResearchAgent 

logger = logging.getLogger(__name__)
system_logger = logging.getLogger('system_log') # Get the specific system_log logger

class KnowledgeCurationAgent:
    """
    Agente responsável pela curadoria autônoma e manutenção do grafo de conhecimento.
    """

    def __init__(self):
        self.llm_flash = llm_provider.get_model(settings.models.rag_agent) # Using Flash for general tasks/searches
        self.llm_pro = llm_provider.get_model(settings.models.analysis_agent) # Using Pro for deeper analysis/decision-making

        self.memory = MemoryAgent(agent_id="knowledge_curation_agent")
        self.kg_agent = KnowledgeGraphAgent()
        self.analysis_agent = AnalysisAgent()
        self.research_agent = ResearchAgent() 

        logger.info("KnowledgeCurationAgent initialized.")

    async def perform_daily_update(self):
        """
        Executa a rotina diária de atualização do conhecimento.
        - Busca por novas publicações relevantes.
        - Analisa e compara com o conhecimento existente.
        - Atualiza o grafo autonomamente ou marca conflitos.
        """
        system_logger.info("Iniciando atualização diária do conhecimento...")
        
        # 1. Buscar novas publicações relevantes usando o ResearchAgent
        # NOTA: O método search do ResearchAgent (e suas ferramentas subjacentes) DEVE ser assíncrono.
        # A Task 8.8.2 em TASK.md aborda a refatoração de src/app/tools/web_search.py para assincronicidade.
        search_query = "novas publicações sobre cirurgia bariátrica OR avanços em tratamento de obesidade"
        new_articles = await self.research_agent.search(search_query, search_type="academic")

        if not new_articles:
            system_logger.info("Nenhuma nova publicação relevante encontrada pelo ResearchAgent.")
            return

        for article in new_articles:
            source_id = article["source_identifier"]
            content = article["content"]
            research_topic = "Atualização de Conhecimento Geral"

            system_logger.info(f"Processando artigo: {source_id}")
            
            try:
                # 2. Analyze evidence
                analysis_data = await self.analysis_agent.classify_evidence(content)
                system_logger.info(f"Análise para {source_id}: Nível de Evidência {analysis_data.get('evidence_level')}")

                # 3. Update Knowledge Graph
                await self.kg_agent.update_graph_with_analysis(source_id, analysis_data, research_topic)
                system_logger.info(f"Grafo de conhecimento atualizado com sucesso para {source_id}.")

            except Exception as e:
                system_logger.error(f"Erro ao processar artigo {source_id}: {e}", exc_info=True)

        await self.memory.remember("last_daily_update", str(datetime.now()))
        system_logger.info("Atualização diária do conhecimento concluída.")

    async def perform_quarterly_review(self):
        """
        Executa a revisão trimestral de conflitos no grafo de conhecimento.
        - Busca por novas publicações que possam resolver conflitos marcados.
        - Reavalia e atualiza o grafo.
        """
        system_logger.info("Iniciando revisão trimestral de conflitos...")
        # Placeholder for actual implementation:
        # 1. Query KG for marked conflicts
        # 2. Use ResearchAgent for targeted searches
        # 3. Re-analyze and resolve conflicts
        # 4. Update KG
        # 5. Log decisions
        await self.memory.remember("last_quarterly_review", str(datetime.now()))
        system_logger.info("Revisão trimestral de conflitos concluída (placeholder).")

    async def bootstrap_knowledge(self, initial_articles: List[Dict[str, Any]]):
        """
        Realiza o bootstrapping inicial do grafo de conhecimento com artigos seminais.
        """
        system_logger.info("Iniciando bootstrapping do conhecimento...")
        # Placeholder for actual implementation:
        # For each article in initial_articles:
        #   1. Extract text
        #   2. Analyze evidence (analysis_agent.classify_evidence)
        #   3. Update KG (kg_agent.update_graph_with_analysis)
        #   4. Log progress
        system_logger.info(f"Bootstrapping concluído para {len(initial_articles)} artigos (placeholder).")

# Example usage (for testing purposes, not part of the main application flow)
async def main():
    curation_agent = KnowledgeCurationAgent()
    await curation_agent.perform_daily_update()
    await curation_agent.perform_quarterly_review()
    # await curation_agent.bootstrap_knowledge(initial_articles=[{"content": "Example article content"}])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
