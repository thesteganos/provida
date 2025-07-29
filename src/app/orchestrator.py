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
    # Build the research graph which defines the workflow for deep research
    graph = build_research_graph()
    
    # Initialize the research state with the provided topic and optional search limit
    initial_state = ResearchState(
        topic=topic,
        research_plan={},  # Placeholder for the research plan
        collected_data=[],  # Placeholder for collected data
        analyzed_data=[],  # Placeholder for analyzed data
        final_report=None,  # Placeholder for the final report
        verification_report=None,  # Placeholder for the verification report
        search_limit=search_limit,  # Pass search_limit to ResearchState
    )
    
    # Invoke the graph with the initial state to start the deep research process
    return await graph.ainvoke(initial_state)