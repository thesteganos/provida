from app.orchestrator_graph import build_research_graph, ResearchState
from typing import Dict, Any

def run_deep_research(topic: str) -> Dict[str, Any]:
    """
    Executa o modo de pesquisa profunda e retorna o estado final.

    Args:
        topic (str): O tópico para a pesquisa.

    Returns:
        Dict[str, Any]: O estado final do grafo de pesquisa.
    """
    graph = build_research_graph()
    initial_state = ResearchState(
        topic=topic,
        research_plan={},
        collected_data=[],
        analyzed_data=[],
        final_report={},
        verification_report={},
    )

    return graph.invoke(initial_state)
