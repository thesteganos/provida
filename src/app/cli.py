import asyncio
import json
import logging
import datetime
from enum import Enum
from typing import Optional, List
from pathlib import Path
import yaml

import typer
import asyncio_typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from app.config.settings import settings, get_settings, GlobalSettings # Import get_settings and GlobalSettings
from app.models.rag_models import RagResponse
from app.rag import perform_rag_query
from app.orchestrator import run_deep_research
from app.agents.feedback_agent import FeedbackAgent
from app.reporting.utils import export_report_formats

import re

def _slugify(text: str) -> str:
    """
    Converte uma string em um slug URL-friendly.
    """
    text = re.sub(r'[^
\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '_', text)
    return text

# Inicializa o Typer e o Rich Console
app = typer.Typer(
    name="provida",
    help="Pró-Vida: Assistente de Pesquisa Autônomo para Cirurgia Bariátrica.",
    add_completion=False,
)

automation_app = typer.Typer(
    name="automation",
    help="Gerencia as tarefas autônomas de curadoria de conhecimento."
)
app.add_typer(automation_app)

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

def _format_text_for_display(
    text_content: str,
    max_lines: Optional[int] = None,
    highlight_keywords: Optional[str] = None
) -> Text:
    """
    Formata o texto para exibição na CLI, aplicando truncamento e destaque de palavras-chave.

    Args:
        text_content (str): O conteúdo de texto a ser formatado.
        max_lines (Optional[int]): O número máximo de linhas a serem exibidas. Se o texto exceder,
                                    ele será truncado.
        highlight_keywords (Optional[str]): Uma string de palavras-chave separadas por vírgulas para destacar.

    Returns:
        Text: Um objeto Rich Text formatado.
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
        import re
        keywords = [re.escape(k.strip()) for k in highlight_keywords.split(',') if k.strip()]
        for keyword in keywords:
            formatted_text.highlight_regex(f"\\b{keyword}\\b", "bold yellow reverse")

    return formatted_text

async def _prompt_for_feedback(
    query: str,
    response_summary: str,
    agent_type: str
):
    """
    Solicita feedback ao usuário e o coleta usando o FeedbackAgent.

    Args:
        query (str): A consulta original ou tópico da pesquisa.
        response_summary (str): O resumo da resposta fornecida ao usuário.
        agent_type (str): O tipo de agente que gerou a resposta (e.g., "RAG", "Deep Research").
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

    Args:
        updated_settings (GlobalSettings): O objeto de configurações Pydantic atualizado.
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


@automation_app.command("enable")
def automation_enable():
    """Ativa a execução de tarefas autônomas."""
    current_settings = get_settings()
    current_settings.automation.enabled = True
    _write_config_to_yaml(current_settings)
    console.print("[bold green]Automação ativada.[/bold green]")

@automation_app.command("disable")
def automation_disable():
    """Desativa a execução de tarefas autônomas."""
    current_settings = get_settings()
    current_settings.automation.enabled = False
    _write_config_to_yaml(current_settings)
    console.print("[bold red]Automação desativada.[/bold red]")

@automation_app.command("set-cron")
def automation_set_cron(
    daily: str = typer.Option(..., help="Cron string para atualização diária (ex: '0 5 * * *')."),
    quarterly: str = typer.Option(..., help="Cron string para revisão trimestral (ex: '0 6 1 */3 *')."),
):
    """Define os horários de execução das tarefas autônomas usando cron strings."""
    current_settings = get_settings()
    current_settings.automation.daily_update_cron = daily
    current_settings.automation.quarterly_review_cron = quarterly
    _write_config_to_yaml(current_settings)
    console.print("[bold green]Horários de cron atualizados.[/bold green]")
    console.print(f"  Atualização Diária: [cyan]{daily}[/cyan]")
    console.print(f"  Revisão Trimestral: [cyan]{quarterly}[/cyan]")


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
    except ConnectionError as e:
        console.print(f"[bold red]Erro de Conexão:[/bold red] {e}")
    except RuntimeError as e:
        console.print(f"[bold red]Erro de Execução:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro inesperado no modo de consulta rápida:[/bold red]\n{e}")
        logger.error("Erro inesperado no modo de consulta rápida", exc_info=True)
    finally:
        if output_format == OutputFormat.text and response_summary:
            asyncio.run(_prompt_for_feedback(query, response_summary, "RAG"))


@app.command(name="profunda")
@asyncio_typer.wrap_async()
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
            final_state = await run_deep_research(topic, search_limit)

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

            # Export to requested formats
            export_formats = []
            if pdf_output:
                export_formats.append("pdf")
            if docx_output:
                export_formats.append("docx")
            if markdown_output:
                export_formats.append("markdown")

            if export_formats:
                export_report_formats(topic, report_summary, citations, export_formats)

    except (ValueError, ConnectionError) as e:
        console.print(f"[bold red]Erro durante a configuração ou execução da pesquisa:[/bold red] {e}")
        logger.error(f"Erro de configuração ou conexão na pesquisa profunda: {e}", exc_info=True)
    except Exception as e:
        console.print(f"[bold red]Ocorreu um erro crítico durante a orquestração da pesquisa profunda:[/bold red]\n{e}")
        logger.error("Erro crítico na orquestração da pesquisa profunda", exc_info=True)
    finally:
        if output_format == OutputFormat.text and report_summary:
            asyncio.run(_prompt_for_feedback(topic, report_summary, "Deep Research"))


def main():
    console.print(Panel(f"[bold]Sistema Pró-Vida[/bold]\nProvider LLM: [cyan]{settings.llm_provider}[/cyan]", border_style="blue"))
    app()
    console.print("\n[bold green]Operação concluída.[/bold green]")


if __name__ == "__main__":
    main()