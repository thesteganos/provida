from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MarkdownExporter:
    """
    Classe para exportar relatórios de pesquisa para Markdown.
    """
    def export_report(self, final_report: Dict[str, Any], output_filename: str = "report.md") -> bool:
        """
        Exporta o relatório final para um arquivo Markdown.
        """
        logger.info(f"Exportando relatório para Markdown: {output_filename}")
        
        content = []
        content.append(f"# Relatório de Pesquisa Pró-Vida\n")
        content.append(f"## Tópico: {final_report.get('research_question', 'N/A')}\n")
        content.append(f"Data de Geração: {final_report.get('generation_date', 'N/A')}\n\n")

        content.append(f"## Resumo Final\n")
        content.append(f"{final_report.get('summary', 'Nenhum resumo disponível.')}\n\n")

        citations = final_report.get('citations_used', [])
        if citations:
            content.append(f"## Citações Utilizadas\n")
            for c in citations:
                citation_text = f"- [ID: {c.get('id')}] {c.get('sentence_in_summary')}"
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
