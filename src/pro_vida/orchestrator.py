import logging
import asyncio
from typing import TypedDict, Annotated, List, Optional
import operator

from pro_vida.agents.research_agent import ResearchAgent

logger = logging.getLogger(__name__)

# Define o estado do grafo
class AgentState(TypedDict):
    topic: str
    research_results: List[dict]

class DeepResearchOrchestrator:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def _build_graph(self):
        """Constrói o grafo de orquestração com LangGraph."""
        workflow = StateGraph(AgentState)

        # Adiciona o nó de pesquisa
        workflow.add_node("research_node", self.run_research_agent)

        # Define o ponto de entrada e o ponto final
        workflow.set_entry_point("research_node")
        workflow.add_edge("research_node", END)

        # Compila o grafo
        return workflow.compile()

    def run_research_agent(self, state: AgentState):
        """Executa o agente de pesquisa."""
        logger.info("Orquestrador: Executando o nó de pesquisa.")
        topic = state['topic']

        if self.loop is None:
            raise RuntimeError("Event loop not configured")
        results = self.loop.run_until_complete(
            self.research_agent.search_web(topic)
        )

        return {"research_results": results}

    def run(
        self,
        topic: str,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> List[dict]:
        """Inicia a execução do fluxo de pesquisa profunda."""
        logger.info(f"Iniciando orquestrador para o tópico: {topic}")

        self.loop = loop or asyncio.get_event_loop()
        workflow = self._build_graph()

        initial_state = {"topic": topic}

        # O LangGraph gerencia a execução dos nós.
        final_state = workflow.invoke(initial_state)

        logger.info("Orquestração concluída.")
        return final_state.get("research_results", [])
