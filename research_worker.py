# research_worker.py
"""
Este módulo implementa o Agente de Pesquisa Autônomo do sistema PROVIDA.

O agente é projetado para rodar periodicamente (agendado com `schedule`),
buscando novos artigos científicos relevantes no PubMed. Para cada tema de
interesse configurado, ele:
1. Busca artigos no PubMed usando a ferramenta `PubMedQueryRun` e `Bio.Entrez`.
2. Para cada artigo encontrado, utiliza um LLM (agente crítico/analisador) para:
    a. Determinar a relevância clínica do artigo.
    b. Gerar um resumo em português.
    c. Tentar extrair uma URL para o PDF do texto completo (usando Entrez e regex).
3. Se um artigo for relevante e uma URL de PDF for encontrada, o PDF é baixado.
4. O documento baixado é então ingerido na base de conhecimento RAG através
   do `KnowledgeBaseManager`.

Principais componentes:
- `ArticleAnalysis`: Modelo Pydantic para estruturar a análise do LLM sobre um artigo.
- `ResearchAgent`: Classe que encapsula a lógica do agente de pesquisa.
- Agendamento de tarefas com `schedule` para execução periódica.

O objetivo é manter a base de conhecimento do sistema atualizada.
"""
import schedule
import time
import os
import hashlib
import re
import logging
from urllib.request import Request, urlopen, HTTPError
from urllib.parse import urlparse, urljoin # Adicionado urljoin
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
import xml.etree.ElementTree as ET # Para parsear XML do Entrez

load_dotenv()
logger = logging.getLogger(__name__)

# LangChain e componentes relacionados
# MODIFICADO: Importações da LangChain e Pydantic atualizadas
from langchain_core.prompts import ChatPromptTemplate
# AVISO DE DEPRECIAÇÃO CORRIGIDO: Importando de pydantic.v1
from pydantic.v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
# IMPORT ERROR CORRIGIDO: OutputParserException movido para langchain_core.exceptions
from langchain_core.exceptions import OutputParserException
from langchain.output_parsers import OutputFixingParser


# Módulos locais
from config_loader import config
from kb_manager import kb_manager

# Configurações da API Entrez (PubMed)
ENTREZ_EMAIL: str = config._config.get('entrez_api', {}).get('email', "seu_email_nao_configurado@example.com")
ENTREZ_API_KEY: Optional[str] = config._config.get('entrez_api', {}).get('api_key')

# Configurar Bio.Entrez globalmente
try:
    from Bio import Entrez
    Entrez.email = ENTREZ_EMAIL
    if ENTREZ_API_KEY:
        Entrez.api_key = ENTREZ_API_KEY
    logger.info(f"Bio.Entrez configurado com email: {Entrez.email} e API Key: {'Sim' if ENTREZ_API_KEY else 'Não'}")
except ImportError:
    logger.warning("Módulo BioPython (Bio.Entrez) não encontrado. Extração avançada de PDF via Entrez não estará disponível.")
    Entrez = None # type: ignore
except Exception as e:
    logger.error(f"Erro ao configurar Bio.Entrez: {e}")
    Entrez = None # type: ignore

# Para parsear HTML (se necessário para páginas de editor)
try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.warning("BeautifulSoup não encontrado. Extração de PDF de páginas HTML de editores pode ser limitada.")
    BeautifulSoup = None # type: ignore


class ArticleAnalysis(BaseModel):
    """
    Modelo Pydantic para estruturar o resultado da análise de um artigo científico pelo LLM.
    """
    is_relevant: bool = Field(description="True se o artigo for clinicamente relevante para obesidade e doenças metabólicas.")
    summary_pt: str = Field(description="Resumo conciso do artigo em português (máximo 3-4 frases).")
    reasoning: str = Field(description="Justificativa curta para a decisão de relevância ou não relevância.")
    # pdf_url não é mais pedido ao LLM, será extraído por outras lógicas.

class ResearchAgent:
    """
    Encapsula a lógica do agente de pesquisa autônomo.
    """
    def __init__(self):
        # A ferramenta pubmed_tool foi removida em favor do uso direto de Bio.Entrez
        try:
            self.analyzer_llm = config.get_llm("critique_agent")
        except ValueError as e:
            logger.critical(f"Falha ao carregar LLM 'critique_agent': {e}. ResearchAgent não pode operar.", exc_info=True)
            raise SystemExit(f"Falha ao carregar LLM para ResearchAgent: {e}") from e

        self.analysis_parser = PydanticOutputParser(pydantic_object=ArticleAnalysis)
        self.output_fixing_parser = OutputFixingParser.from_llm(
            parser=self.analysis_parser, llm=self.analyzer_llm, max_retries=2
        )

        # Prompt atualizado para não pedir mais a URL do PDF ao LLM
        self.analysis_prompt = ChatPromptTemplate.from_template(
            "Você é um assistente de pesquisa especializado em medicina metabólica. Analise o seguinte título e abstract de um artigo científico em relação aos tópicos de interesse: {topics}. "
            "Determine se o artigo possui alta relevância clínica e apresenta evidências fortes (ex: ensaios clínicos randomizados, meta-análises, diretrizes de grandes sociedades). "
            "Forneça um resumo conciso em português (3-4 frases).\n\n"
            "Título: {title}\n\n"
            "Abstract:\n{abstract}\n\n{format_instructions}",
            partial_variables={"format_instructions": self.analysis_parser.get_format_instructions()}
        )

    def _extract_data_from_xml_article(self, article_xml: ET.Element) -> Dict[str, Optional[str]]:
        """Extrai dados relevantes de um único nó de artigo XML do PubMed."""
        data = {
            "pmid": None,
            "doi": None,
            "pmcid": None,
            "title": "Título não disponível",
            "abstract": "Abstract não disponível."
        }
        
        # PMID
        pmid_node = article_xml.find(".//MedlineCitation/PMID")
        if pmid_node is not None:
            data["pmid"] = pmid_node.text

        # Título
        title_node = article_xml.find(".//Article/ArticleTitle")
        if title_node is not None:
            data["title"] = "".join(title_node.itertext()).strip()

        # Abstract
        abstract_node = article_xml.find(".//Article/Abstract/AbstractText")
        if abstract_node is not None:
            # Concatena múltiplos parágrafos do abstract se existirem
            data["abstract"] = "\n".join(node.text for node in article_xml.findall(".//Article/Abstract/AbstractText") if node.text)

        # IDs (DOI, PMCID)
        for an_id in article_xml.findall(".//Article/ELocationID") + article_xml.findall(".//PubmedData/ArticleIdList/ArticleId"):
            id_type = an_id.attrib.get("IdType")
            if id_type == "doi" and an_id.text:
                data["doi"] = an_id.text
            elif id_type == "pmc" and an_id.text:
                data["pmcid"] = an_id.text
        
        if not data["abstract"] or data["abstract"].isspace():
            data["abstract"] = "Abstract não disponível."

        logger.debug(f"Dados extraídos do XML para PMID {data['pmid']}: Título='{data['title'][:30]}...', DOI={data['doi']}, PMCID={data['pmcid']}")
        return data


    def _fetch_pubmed_xml(self, pmid: str) -> Optional[ET.ElementTree]:
        """Busca o registro XML completo do PubMed para um dado PMID usando Entrez."""
        if not Entrez:
            logger.warning("Bio.Entrez não está disponível, não é possível buscar XML do PubMed.")
            return None
        try:
            logger.debug(f"Buscando XML do PubMed para PMID: {pmid} via Entrez efetch...")
            handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="xml")
            xml_data = ET.parse(handle)
            handle.close()
            logger.info(f"XML do PubMed para PMID {pmid} obtido com sucesso.")
            return xml_data
        except Exception as e:
            logger.error(f"Erro ao buscar XML do PubMed para PMID {pmid} via Entrez: {e}", exc_info=True)
            return None

    def _extract_pdf_url_from_entrez_xml(self, xml_data: ET.ElementTree) -> Optional[str]:
        """Tenta extrair uma URL de PDF ou link para texto completo do XML do Entrez."""
        if xml_data is None:
            return None

        root = xml_data.getroot()
        # Tenta encontrar links para PMC que geralmente têm PDFs
        for article_id in root.findall(".//ArticleId[@IdType='pmc']"):
            pmcid = article_id.text
            if pmcid:
                pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
                logger.info(f"Encontrado link PMC via XML: {pmc_url}. Verificando PDF...")
                # Tenta encontrar um link de PDF direto no XML (menos comum, mas possível)
                for link in root.findall(".//ArticleLink[contains(@ProviderId, 'PubMed Central')]/Url"): # Heurística
                     if link.text and link.
