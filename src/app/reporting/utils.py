import datetime
from typing import List, Dict, Any

from .pdf_exporter import PDFExporter
from .docx_exporter import DOCXExporter
from .markdown_exporter import MarkdownExporter
from ..cli import _slugify

def export_report_formats(
    topic: str,
    report_summary: str,
    citations: List[Dict[str, Any]],
    formats: List[str],
) -> None:
    """
    Exporta o relatório final para os formatos especificados.

    Args:
        topic (str): O tópico da pesquisa.
        report_summary (str): O resumo do relatório.
        citations (List[Dict[str, Any]]): As citações usadas no relatório.
        formats (List[str]): Uma lista de formatos para exportar (ex: ['pdf', 'docx']).
    """
    if not formats:
        return

    report_data = {
        "research_question": topic,
        "generation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": report_summary,
        "citations_used": citations,
    }

    output_filename_base = f"relatorio_{_slugify(topic)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if "pdf" in formats:
        pdf_exporter = PDFExporter()
        output_filename = f"{output_filename_base}.pdf"
        if pdf_exporter.export_report(report_data, output_filename):
            print(f"[bold green]Relatório exportado para PDF:[/bold green] {output_filename}")
        else:
            print("[bold red]Falha ao exportar relatório para PDF.[/bold red]")

    if "docx" in formats:
        docx_exporter = DOCXExporter()
        output_filename = f"{output_filename_base}.docx"
        if docx_exporter.export_report(report_data, output_filename):
            print(f"[bold green]Relatório exportado para DOCX:[/bold green] {output_filename}")
        else:
            print("[bold red]Falha ao exportar relatório para DOCX.[/bold red]")

    if "markdown" in formats:
        markdown_exporter = MarkdownExporter()
        output_filename = f"{output_filename_base}.md"
        if markdown_exporter.export_report(report_data, output_filename):
            print(f"[bold green]Relatório exportado para Markdown:[/bold green] {output_filename}")
        else:
            print("[bold red]Falha ao exportar relatório para Markdown.[/bold red]")
