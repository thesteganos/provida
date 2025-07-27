import argparse
import argparse
from rich.console import Console
from dotenv import load_dotenv

# Carrega variáveis de ambiente de .env.example ou .env
load_dotenv(dotenv_path='.env.example')
load_dotenv()

# Imports do projeto devem vir depois do load_dotenv
from app.config.settings import settings

def main():
    """Função principal que gerencia a CLI."""
    console = Console()

    console.print("[bold green]Iniciando o sistema Pró-Vida...[/bold green]")
    console.print(f"LLM Provider: [cyan]{settings.get('llm_provider')}[/cyan]")

    parser = argparse.ArgumentParser(description="Pró-Vida: Assistente de Pesquisa Autônomo.")
    parser.add_argument('--mode', required=True, choices=['fast-query', 'deep-research'], help="Modo de operação.")
    parser.add_argument('--query', help="A pergunta para o modo 'fast-query'.")
    parser.add_argument('--topic', help="O tópico para o modo 'deep-research'.")

    args = parser.parse_args()

    if args.mode == 'fast-query':
        if not args.query:
            console.print("[bold red]Erro: O modo 'fast-query' requer o argumento --query.[/bold red]")
            return
        from app.services import run_fast_query
        run_fast_query(args.query)

    elif args.mode == 'deep-research':
        if not args.topic:
            console.print("[bold red]Erro: O modo 'deep-research' requer o argumento --topic.[/bold red]")
            return
        from app.orchestrator import run_deep_research
        run_deep_research(args.topic)

if __name__ == "__main__":
    main()
