from app.models.research_models import FinalReport
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MarkdownExporter:
    """
    Classe para exportar relatórios de pesquisa para Markdown.
    """
    def export_report(self, final_report: FinalReport, output_filename: str = "report.md") -> bool:
        """
        Exporta o relatório final para um arquivo Markdown.

        Args:
            final_report (FinalReport): O objeto FinalReport contendo os dados do relatório.
            output_filename (str): O nome do arquivo de saída (padrão: "report.md").

        Returns:
            bool: True se o relatório foi exportado com sucesso, False caso contrário.
        """
        logger.info(f"Exportando relatório para Markdown: {output_filename}")
        
        content = []
        content.append(f"# Relatório de Pesquisa Pró-Vida\n")
        content.append(f"## Tópico: {final_report.research_question}\n")
        content.append(f"Data de Geração: {final_report.generation_date}\n\n")

        content.append(f"## Resumo Final\n")
        content.append(f"{final_report.summary}\n\n")

        citations = final_report.citations_used
        if citations:
            content.append(f"## Citações Utilizadas\n")
            for c in citations:
                citation_text = f"- [ID: {c.id}] {c.sentence_in_summary}"
                content.append(f"{citation_text}\n")
            content.append(f"\n")

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write("".join(content))
            logger.info(f"Relatório Markdown salvo em {output_filename}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar o relatório Markdown: {e}", exc_info=True)
            return False
