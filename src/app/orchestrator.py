from app.orchestrator_graph import build_research_graph, ResearchState
from app.models.research_models import FinalReport, VerificationReport
from typing import Dict, Any, Optional

async def run_deep_research(topic: str, search_limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Executa o modo de pesquisa profunda e retorna o estado final.

    Args:
        topic (str): O tópico para a pesquisa.
        search_limit (Optional[int]): Limite de buscas para a pesquisa profunda.

    Returns:
        Dict[str, Any]: O estado final do grafo de pesquisa.
    """
    graph = build_research_graph()
    initial_state = ResearchState(
        topic=topic,
        research_plan={},
        collected_data=[],
        analyzed_data=[],
        final_report=None,
        verification_report=None,
        search_limit=search_limit, # Pass search_limit to ResearchState
    )

    return await graph.ainvoke(initial_state)