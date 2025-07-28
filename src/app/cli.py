import asyncio
import json
import logging
from enum import Enum
from typing import Optional, List
from pathlib import Path
import yaml

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from app.config.settings import settings, get_settings, GlobalSettings # Import get_settings and GlobalSettings
from app.models.rag_models import RagResponse
from app.rag import perform_rag_query
from app.orchestrator import run_deep_research
from app.agents.feedback_agent import FeedbackAgent
from app.reporting.pdf_exporter import PDFExporter
from app.reporting.docx_exporter import DOCXExporter
from app.reporting.markdown_exporter import MarkdownExporter

# Inicializa o Typer e o Rich Console
app = typer.Typer(
    name="provida",
    help="Pró-Vida: Assistente de Pesquisa Autônomo para Cirurgia Bariátrica.",
    add_completion=False,
)
console = Console()
logger = logging.getLogger(__name__)

feedback_agent = FeedbackAgent()

class OutputFormat(str, Enum):
    text = "text"
    json = "json"

class DetailLevel(str, Enum):
    breve = "breve"
    padrao = "padrao"
    detalhado = "detalhado"

def _format_text_for_display(text_content: str, max_lines: Optional[int] = None, highlight_keywords: Optional[str] = None) -> Text:
    """
    Formata o texto para exibição na CLI, aplicando truncamento e destaque de palavras-chave.
    """
    lines = text_content.splitlines()
    original_line_count = len(lines)
    
    if max_lines is not None and original_line_count > max_lines:
        lines = lines[:max_lines]
        truncated_text = "\n".join(lines) + f"\n[dim]... (truncated {original_line_count - max_lines} lines)[/dim]"
    else:
        truncated_text = text_content

    formatted_text = Text(truncated_text, justify="left")

    if highlight_keywords:
        keywords = [k.strip() for k in highlight_keywords.split(',') if k.strip()]
        for keyword in keywords:
            formatted_text.highlight_regex(f"\\b{keyword}\\b", "bold yellow reverse")

    return formatted_text

async def _prompt_for_feedback(query: str, response_summary: str, agent_type: str):
    """
    Prompt the user for feedback and collect it using the FeedbackAgent.
    """
    console.print("\n[bold blue]Gostaria de fornecer feedback sobre esta interação?[/bold blue]")
    provide_feedback = Prompt.ask("[bold blue]Digite 's' para sim ou 'n' para não[/bold blue]", choices=["s", "n"], default="n")

    if provide_feedback.lower() == "s":
        feedback_text = Prompt.ask("[bold blue]Por favor, digite seu feedback[/bold blue]")
        context = {
            "query": query,
            "response_summary": response_summary,
            "agent_type": agent_type
        }
        try:
            structured_feedback = await feedback_agent.collect_feedback(feedback_text, context)
            console.print("[bold green]Feedback recebido! Obrigado por sua contribuição.[/bold green]")
            logger.info(f"Feedback estruturado coletado: {structured_feedback}")
        except Exception as e:
            console.print(f"[bold red]Erro ao coletar feedback: {e}[/bold red]")
            logger.error(f"Erro ao coletar feedback: {e}", exc_info=True)


def _write_config_to_yaml(updated_settings: GlobalSettings):
    """
    Escreve as configurações atualizadas de volta para o config.yaml.
    """
    config_path = Path(__file__).parent.parent.parent.parent / 'config.yaml'
    try:
        # Convert Pydantic model to dictionary, excluding default values if desired
        config_dict = updated_settings.model_dump(exclude_unset=True)
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, sort_keys=False, indent=2)
        console.print(f"[bold green]Configurações salvas em:[/bold green] {config_path}")
        logger.info(f"Configurações salvas em {config_path}")
    except Exception as e:
        console.print(f"[bold red]Erro ao salvar configurações: {e}[/bold red]")
        logger.error(f"Erro ao salvar configurações: {e}", exc_info=True)


@app.command(name="rapida")
def fast_query(
    query: str = typer.Argument(..., help="A pergunta para a consulta rápida baseada em RAG."),
    detail_level: DetailLevel = typer.Option(
        DetailLevel.padrao,
        "--detail-level",
        "-d",
        help="Nível de detalhe para o resumo (breve, padrao, detalhado).",
        case_sensitive=False,
    ),
    max_lines: Optional[int] = typer.Option(
        None,
        "--max-lines",
        "-ml",
        help="Número máximo de linhas para exibir no resumo e fontes.",
    ),
    highlight_keywords: Optional[str] = typer.Option(
        None,
        "--highlight",
        "-hl",
        help="Palavras-chave para destacar no texto (separadas por vírgula).",
    ),
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

    response_summary = ""
    try:
        response: RagResponse = asyncio.run(perform_rag_query(query, detail_level))
        response_summary = response.summary

        if output_format == OutputFormat.json:
            console.print(response.model_dump_json(indent=2))
            return

        summary_panel = Panel(
            _format_text_for_display(response.summary, max_lines, highlight_keywords),
            title="[bold green]Resumo da Resposta[/bold green]",
            border_style="green",
            expand=True,
        )
        console.print(summary_panel)

        if response.sources:
            sources_text = "\n".join(f"- {source}" for source in response.sources)
            sources_panel = Panel(
                _format_text_for_display(sources_text, max_lines, highlight_keywords),
                title="[bold yellow]Fontes Consultadas[/bold yellow]",
                border_style="yellow",
                expand=True,
            )
            console.print(sources_panel)

    except ValueError as e:
        console.print(f"[bold red]Erro de Validação:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro inesperado:[/bold red]\n{e}")
    finally:
        if output_format == OutputFormat.text and response_summary:
            asyncio.run(_prompt_for_feedback(query, response_summary, "RAG"))


@app.command(name="profunda")
def deep_research(
    topic: str = typer.Argument(..., help="O tópico para a pesquisa profunda."),
    search_limit: Optional[int] = typer.Option(
        None,
        "--search-limit",
        "-l",
        help="Limite de buscas para o modo de pesquisa profunda (padrão: configurado no sistema).",
    ),
    max_lines: Optional[int] = typer.Option(
        None,
        "--max-lines",
        "-ml",
        help="Número máximo de linhas para exibir no resumo e fontes.",
    ),
    highlight_keywords: Optional[str] = typer.Option(
        None,
        "--highlight",
        "-hl",
        help="Palavras-chave para destacar no texto (separadas por vírgula).",
    ),
    pdf_output: bool = typer.Option(
        False,
        "--pdf-output",
        "-p",
        help="Exportar o relatório final para PDF.",
    ),
    docx_output: bool = typer.Option(
        False,
        "--docx-output",
        "-d",
        help="Exportar o relatório final para DOCX.",
    ),
    markdown_output: bool = typer.Option(
        False,
        "--markdown-output",
        "-m",
        help="Exportar o relatório final para Markdown.",
    ),
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
    report_summary = ""
    try:
        with console.status(f"[bold green]Executando Pesquisa Profunda sobre: '[cyan]{topic}[/cyan]\'...", spinner="dots"):
            final_state = run_deep_research(topic, search_limit)

            if output_format == OutputFormat.json:
                console.print(json.dumps(final_state, indent=2, default=str))
                return

            report = final_state.get("final_report", {})
            report_summary = report.get("summary", "")

            if not report or "error" in report:
                error_message = report.get("error", "Relatório final não foi gerado.")
                console.print(f"[bold red]Erro na Pesquisa Profunda:[/bold red] {error_message}")
                return

            summary_panel = Panel(
                _format_text_for_display(report_summary, max_lines, highlight_keywords),
                title="[bold green]Relatório Final[/bold green]",
                border_style="green",
                expand=True,
            )
            console.print(summary_panel)

            citations = report.get("citations_used", [])
            if citations:
                citations_text = "\n".join(f"- [ID: {c.get('id')}] {c.get('sentence_in_summary')}" for c in citations)
                citations_panel = Panel(
                    _format_text_for_display(citations_text, max_lines, highlight_keywords),
                    title="[bold yellow]Citações Utilizadas[/bold yellow]",
                    border_style="yellow",
                    expand=True,
                )
                console.print(citations_panel)

            # Export to PDF
            if pdf_output:
                pdf_exporter = PDFExporter()
                pdf_report_data = {
                    "research_question": topic,
                    "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": report_summary,
                    "citations_used": citations
                }
                output_filename = f"relatorio_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                if pdf_exporter.export_report(pdf_report_data, output_filename):
                    console.print(f"[bold green]Relatório exportado para PDF:[/bold green] {output_filename}")
                else:
                    console.print("[bold red]Falha ao exportar relatório para PDF.[/bold red]")

            # Export to DOCX
            if docx_output:
                docx_exporter = DOCXExporter()
                docx_report_data = {
                    "research_question": topic,
                    "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": report_summary,
                    "citations_used": citations
                }
                output_filename = f"relatorio_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                if docx_exporter.export_report(docx_report_data, output_filename):
                    console.print(f"[bold green]Relatório exportado para DOCX:[/bold green] {output_filename}")
                else:
                    console.print("[bold red]Falha ao exportar relatório para DOCX.[/bold red]")

            # Export to Markdown
            if markdown_output:
                markdown_exporter = MarkdownExporter()
                markdown_report_data = {
                    "research_question": topic,
                    "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": report_summary,
                    "citations_used": citations
                }
                output_filename = f"relatorio_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                if markdown_exporter.export_report(markdown_report_data, output_filename):
                    console.print(f"[bold green]Relatório exportado para Markdown:[/bold green] {output_filename}")
                else:
                    console.print("[bold red]Falha ao exportar relatório para Markdown.[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro crítico durante a orquestração:[/bold red]\n{e}")
    finally:
        if output_format == OutputFormat.text and report_summary:
            asyncio.run(_prompt_for_feedback(topic, report_summary, "Deep Research"))


def main():
    console.print(Panel(f"[bold]Sistema Pró-Vida[/bold]\nProvider LLM: [cyan]{settings.llm_provider}[/cyan]", border_style="blue"))
    app()
    console.print("\n[bold green]Operação concluída.[/bold green]")


if __name__ == "__main__":
    import datetime # Import datetime here for pdf_output
    main()