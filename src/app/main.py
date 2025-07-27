import argparse
import asyncio
from rich.console import Console
from dotenv import load_dotenv

# Carrega variáveis de ambiente de .env.example ou .env
load_dotenv(dotenv_path='.env.example')
load_dotenv()

# Imports do projeto devem vir depois do load_dotenv
from pro_vida.agents.research_agent import ResearchAgent
from pro_vida.config.settings import settings

def run_fast_query(query: str, console: Console):
    """Executa o modo de consulta rápida."""
    console.print(f"Executando Consulta Rápida para: '{query}'")

    # Esta é uma implementação provisória.
    # No futuro, isso usará um handler RAG.
    agent = ResearchAgent()

    # Como o search_web é async, precisamos de um loop de eventos
    results = asyncio.run(agent.search_web(query))

    console.print("\n[bold]Resultados da Pesquisa:[/bold]")
    console.print(results)

from pro_vida.orchestrator import DeepResearchOrchestrator

def run_deep_research(topic: str, console: Console):
    """Executa o modo de pesquisa profunda."""
    console.print(f"Iniciando Pesquisa Profunda sobre: '{topic}'")

    # Instancia e executa o orquestrador
    orchestrator = DeepResearchOrchestrator()
    loop = asyncio.new_event_loop()
    try:
        final_state = orchestrator.run(topic, loop)
    finally:
        loop.close()

    console.print("\n[bold]Resultados da Orquestração:[/bold]")
    console.print(final_state.get('research_results', 'Nenhum resultado encontrado.'))


def main():
    """Função principal que gerencia a CLI."""
    console = Console()

    parser = argparse.ArgumentParser(description="Pró-Vida: Assistente de Pesquisa Autônomo.")
    parser.add_argument('--mode', required=True, choices=['fast-query', 'deep-research'], help="Modo de operação.")
    parser.add_argument('--query', help="A pergunta para o modo 'fast-query'.")
    parser.add_argument('--topic', help="O tópico para o modo 'deep-research'.")

    args = parser.parse_args()

    console.print("[bold green]Iniciando o sistema Pró-Vida...[/bold green]")
    console.print(f"LLM Provider: [cyan]{settings.get('llm_provider')}[/cyan]")

    if args.mode == 'fast-query':
        if not args.query:
            console.print("[bold red]Erro: O modo 'fast-query' requer o argumento --query.[/bold red]")
            return
        run_fast_query(args.query, console)

    elif args.mode == 'deep-research':
        if not args.topic:
            console.print("[bold red]Erro: O modo 'deep-research' requer o argumento --topic.[/bold red]")
            return
        run_deep_research(args.topic, console)

    console.print("\n[bold green]Operação concluída.[/bold green]")

if __name__ == "__main__":
    main()
