from fpdf import FPDF
from app.models.research_models import FinalReport
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class PDFExporter:
    """
    Classe para exportar relatórios de pesquisa para PDF.
    """
    def __init__(self):
        """
        Inicializa o PDFExporter, configurando um novo documento PDF.
        """
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.add_page()
        self.pdf.set_font("Arial", size=12)

    def add_title(self, title: str):
        """
        Adiciona um título principal ao documento PDF.

        Args:
            title (str): O texto do título.
        """
        self.pdf.set_font("Arial", 'B', 16)
        self.pdf.cell(200, 10, txt=title, ln=True, align='C')
        self.pdf.ln(10)

    def add_section_title(self, title: str):
        """
        Adiciona um título de seção ao documento PDF.

        Args:
            title (str): O texto do título da seção.
        """
        self.pdf.set_font("Arial", 'B', 14)
        self.pdf.cell(200, 10, txt=title, ln=True, align='L')
        self.pdf.ln(5)

    def add_text(self, text: str):
        """
        Adiciona um parágrafo de texto ao documento PDF.

        Args:
            text (str): O texto a ser adicionado.
        """
        self.pdf.set_font("Arial", size=12)
        self.pdf.multi_cell(0, 10, txt=text)
        self.pdf.ln(5)

    def add_citations(self, citations: List[Dict[str, Any]]):
        """
        Adiciona uma seção de citações ao documento PDF.

        Args:
            citations (List[Dict[str, Any]]): Uma lista de dicionários de citação.
        """
        self.add_section_title("Citações Utilizadas")
        for c in citations:
            citation_text = f"- [ID: {c.id}] {c.sentence_in_summary}"
            self.pdf.multi_cell(0, 10, txt=citation_text)
        self.pdf.ln(5)

    def export_report(self, final_report: FinalReport, output_filename: str = "report.pdf"):
        # Ensure final_report is a FinalReport instance
        if not isinstance(final_report, FinalReport):
            logger.error("Invalid input: final_report must be an instance of FinalReport.")
            return False
        """
        Exporta o relatório final para um arquivo PDF.

        Args:
            final_report (FinalReport): O objeto FinalReport contendo os dados do relatório.
            output_filename (str): O nome do arquivo de saída (padrão: "report.pdf").

        Returns:
            bool: True se o relatório foi exportado com sucesso, False caso contrário.
        """
        logger.info(f"Exportando relatório para PDF: {output_filename}")
        
        self.add_title("Relatório de Pesquisa Pró-Vida")
        self.add_section_title(f"Tópico: {final_report.research_question}")
        self.add_text(f"Data de Geração: {final_report.generation_date}")
        self.pdf.ln(10)

        self.add_section_title("Resumo Final")
        self.add_text(final_report.summary)

        citations = final_report.citations_used
        if citations:
            self.add_citations(citations)

        try:
            self.pdf.output(output_filename)
            logger.info(f"Relatório PDF salvo em {output_filename}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar o relatório PDF: {e}", exc_info=True)
            return False

