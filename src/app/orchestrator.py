from rich.console import Console
from app.orchestrator_graph import build_research_graph, ResearchState

def run_deep_research(topic: str):
    """Executa o modo de pesquisa profunda."""
    console = Console()
    console.print(f"Iniciando Pesquisa Profunda sobre: '{topic}'")

    graph = build_research_graph()
    initial_state = ResearchState(
        topic=topic,
        research_plan={},
        collected_data=[],
        analyzed_data=[],
        final_report={}
    )
    
    final_state = graph.invoke(initial_state)

    console.print("\n[bold]Pesquisa Profunda Concluída:[/bold]")
    console.print(final_state)


