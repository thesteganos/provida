import asyncio
import json
from enum import Enum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from app.config.settings import settings
from app.models.rag_models import RagResponse
from app.rag import perform_rag_query
from app.orchestrator import run_deep_research

# Inicializa o Typer e o Rich Console
app = typer.Typer(
    name="provida",
    help="Pró-Vida: Assistente de Pesquisa Autônomo para Cirurgia Bariátrica.",
    add_completion=False,
)
console = Console()

class OutputFormat(str, Enum):
    text = "text"
    json = "json"


@app.command(name="rapida")
def fast_query(
    query: str = typer.Argument(..., help="A pergunta para a consulta rápida baseada em RAG."),
    output_format: OutputFormat = typer.Option(
        OutputFormat.text,
        "--output-format",
        "-o",
        help="Formato da saída (text ou json).",
        case_sensitive=False,
    ),
):
    """
    Executa uma consulta rápida na base de conhecimento para obter respostas diretas.
    """
    console.print(f"Executando Consulta Rápida para: '[cyan]{query}[/cyan]'")

    try:
        # Chama a função RAG assíncrona
        response: RagResponse = asyncio.run(perform_rag_query(query))

        if output_format == OutputFormat.json:
            # Imprime a saída como um JSON formatado
            console.print(response.model_dump_json(indent=2))
            return

        # Formata e exibe a resposta
        summary_panel = Panel(
            Text(response.summary, justify="left"),
            title="[bold green]Resumo da Resposta[/bold green]",
            border_style="green",
            expand=True,
        )
        console.print(summary_panel)

        if response.sources:
            sources_text = "\n".join(f"- {source}" for source in response.sources)
            sources_panel = Panel(
                Text(sources_text),
                title="[bold yellow]Fontes Consultadas[/bold yellow]",
                border_style="yellow",
                expand=True,
            )
            console.print(sources_panel)

    except ValueError as e:
        console.print(f"[bold red]Erro de Validação:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro inesperado:[/bold red]\n{e}")


@app.command(name="profunda")
def deep_research(
    topic: str = typer.Argument(..., help="O tópico para a pesquisa profunda."),
    output_format: OutputFormat = typer.Option(
        OutputFormat.text,
        "--output-format",
        "-o",
        help="Formato da saída (text ou json).",
        case_sensitive=False,
    ),
):
    """
    Inicia uma pesquisa profunda e exaustiva sobre um tópico.
    """
    with console.status(f"[bold green]Executando Pesquisa Profunda sobre: '[cyan]{topic}[/cyan]'...", spinner="dots"):
        try:
            final_state = run_deep_research(topic)

            if output_format == OutputFormat.json:
                console.print(json.dumps(final_state, indent=2, default=str)) # default=str para lidar com tipos não serializáveis
                return

            report = final_state.get("final_report", {})

            if not report or "error" in report:
                error_message = report.get("error", "Relatório final não foi gerado.")
                console.print(f"[bold red]Erro na Pesquisa Profunda:[/bold red] {error_message}")
                return

            summary_panel = Panel(
                Text(report.get("summary", "Nenhum resumo disponível."), justify="left"),
                title="[bold green]Relatório Final[/bold green]",
                border_style="green",
                expand=True,
            )
            console.print(summary_panel)

            citations = report.get("citations_used", [])
            if citations:
                citations_text = "\n".join(f"- [ID: {c.get('id')}] {c.get('sentence_in_summary')}" for c in citations)
                citations_panel = Panel(
                    Text(citations_text),
                    title="[bold yellow]Citações Utilizadas[/bold yellow]",
                    border_style="yellow",
                    expand=True,
                )
                console.print(citations_panel)
        except Exception as e:
            console.print(f"[bold red]Ocorreu um erro crítico durante a orquestração:[/bold red]\n{e}")


def main():
    console.print(Panel(f"[bold]Sistema Pró-Vida[/bold]\nProvider LLM: [cyan]{settings.llm_provider}[/cyan]", border_style="blue"))
    app()
    console.print("\n[bold green]Operação concluída.[/bold green]")


if __name__ == "__main__":
    main()