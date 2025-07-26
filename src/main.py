import argparse
import yaml
from rich.console import Console

# (Aqui viriam os imports dos módulos de agentes, orquestrador, etc.)
# from pro_vida.orchestrator import DeepResearchOrchestrator
# from pro_vida.query_handler import FastQueryHandler

def load_config():
    """Carrega as configurações do arquivo config.yaml."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    """Função principal que gerencia a CLI."""
    console = Console()
    config = load_config()

    parser = argparse.ArgumentParser(description="Pró-Vida: Assistente de Pesquisa Autônomo.")
    parser.add_argument('--mode', required=True, choices=['fast-query', 'deep-research'], help="Modo de operação.")
    parser.add_argument('--query', help="A pergunta para o modo 'fast-query'.")
    parser.add_argument('--topic', help="O tópico para o modo 'deep-research'.")

    args = parser.parse_args()

    console.print("[bold green]Iniciando o sistema Pró-Vida...[/bold green]")

    if args.mode == 'fast-query':
        if not args.query:
            console.print("[bold red]Erro: O modo 'fast-query' requer o argumento --query.[/bold red]")
            return
        # handler = FastQueryHandler(config)
        # response = handler.execute(args.query)
        # console.print(response)
        console.print(f"Executando Consulta Rápida para: '{args.query}'")


    elif args.mode == 'deep-research':
        if not args.topic:
            console.print("[bold red]Erro: O modo 'deep-research' requer o argumento --topic.[/bold red]")
            return
        # orchestrator = DeepResearchOrchestrator(config)
        # orchestrator.run(args.topic)
        console.print(f"Iniciando Pesquisa Profunda sobre: '{args.topic}'")

    console.print("[bold green]Operação concluída.[/bold green]")

if __name__ == "__main__":
    main()
