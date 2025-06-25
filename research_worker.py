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
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
import xml.etree.ElementTree as ET

load_dotenv()
logger = logging.getLogger(__name__)

# LangChain e componentes relacionados
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field # Usando Pydantic v2
from langchain_core.output_parsers import PydanticOutputParser
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
    Entrez = None
except Exception as e:
    logger.error(f"Erro ao configurar Bio.Entrez: {e}")
    Entrez = None

# Para parsear HTML (se necessário para páginas de editor)
try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.warning("BeautifulSoup não encontrado. Extração de PDF de páginas HTML de editores pode ser limitada.")
    BeautifulSoup = None


class ArticleAnalysis(BaseModel):
    """
    Modelo Pydantic para estruturar o resultado da análise de um artigo científico pelo LLM.
    """
    is_relevant: bool = Field(description="True se o artigo for clinicamente relevante para obesidade e doenças metabólicas.")
    summary_pt: str = Field(description="Resumo conciso do artigo em português (máximo 3-4 frases).")
    reasoning: str = Field(description="Justificativa curta para a decisão de relevância ou não relevância.")

class ResearchAgent:
    """
    Encapsula a lógica do agente de pesquisa autônomo.
    """
    def __init__(self):
        try:
            self.analyzer_llm = config.get_llm("critique_agent")
        except ValueError as e:
            logger.critical(f"Falha ao carregar LLM 'critique_agent': {e}. ResearchAgent não pode operar.", exc_info=True)
            raise SystemExit(f"Falha ao carregar LLM para ResearchAgent: {e}") from e

        self.analysis_parser = PydanticOutputParser(pydantic_object=ArticleAnalysis)
        self.output_fixing_parser = OutputFixingParser.from_llm(
            parser=self.analysis_parser, llm=self.analyzer_llm, max_retries=2
        )

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
        
        pmid_node = article_xml.find(".//MedlineCitation/PMID")
        if pmid_node is not None:
            data["pmid"] = pmid_node.text

        title_node = article_xml.find(".//Article/ArticleTitle")
        if title_node is not None:
            data["title"] = "".join(title_node.itertext()).strip()

        abstract_node = article_xml.find(".//Article/Abstract/AbstractText")
        if abstract_node is not None:
            data["abstract"] = "\n".join(node.text for node in article_xml.findall(".//Article/Abstract/AbstractText") if node.text)

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
        for article_id in root.findall(".//ArticleId[@IdType='pmc']"):
            pmcid = article_id.text
            if pmcid:
                pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
                logger.info(f"Encontrado link PMC via XML: {pmc_url}. Esta será a URL alvo.")
                return pmc_url
        
        doi_element = root.find(".//ArticleId[@IdType='doi']")
        if doi_element is not None and doi_element.text:
            doi = doi_element.text
            doi_url = f"https://doi.org/{doi}"
            logger.info(f"DOI encontrado no XML: {doi}. URL: {doi_url}. Esta será a URL alvo.")
            return doi_url

        logger.debug("Nenhuma URL de PDF ou link PMC/DOI promissor encontrado no XML do Entrez.")
        return None

    def _get_pdf_url_from_html_page(self, page_url: str) -> Optional[str]:
        """Tenta encontrar um link de PDF em uma página HTML (ex: página do editor)."""
        if not BeautifulSoup:
            logger.warning("BeautifulSoup não está instalado. Não é possível parsear HTML para encontrar PDF.")
            return None
        try:
            logger.debug(f"Tentando buscar PDF na página HTML: {page_url}")
            req = Request(page_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=20) as response:
                if 200 <= response.status < 300:
                    html_content = response.read()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        if href.lower().endswith(".pdf"):
                            pdf_link = urljoin(page_url, href)
                            logger.info(f"Link PDF encontrado em HTML ({page_url}): {pdf_link}")
                            return pdf_link
                    for a_tag in soup.find_all('a', href=True, string=re.compile(r'pdf|full text', re.I)):
                        href = a_tag['href']
                        if href and not href.lower().startswith('javascript:'):
                             pdf_link = urljoin(page_url, href)
                             logger.info(f"Link PDF (por texto) encontrado em HTML ({page_url}): {pdf_link}")
                             return pdf_link
                    logger.debug(f"Nenhum link PDF óbvio encontrado na página HTML: {page_url}")
                else:
                    logger.warning(f"Falha ao buscar página HTML {page_url}, status: {response.status}")
        except Exception as e:
            logger.error(f"Erro ao tentar buscar/parsear HTML de {page_url}: {e}", exc_info=True)
        return None

    async def _attempt_pdf_extraction(self, article_ids: Dict[str, Optional[str]]) -> Optional[str]:
        """Orquestra as tentativas de extração de URL de PDF a partir dos IDs."""
        
        target_url = None
        if article_ids.get("pmcid"):
            target_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{article_ids['pmcid']}/"
            logger.info(f"PMCID encontrado. Tentando extrair PDF a partir de: {target_url}")

        elif article_ids.get("doi"):
            target_url = f"https://doi.org/{article_ids['doi']}"
            logger.info(f"DOI encontrado. Tentando extrair PDF a partir de: {target_url}")

        if target_url:
            pdf_from_page = self._get_pdf_url_from_html_page(target_url)
            if pdf_from_page:
                return pdf_from_page
            else:
                 logger.warning(f"Não foi possível encontrar um link PDF direto na página do artigo: {target_url}")
        else:
            logger.warning(f"Não foi possível encontrar um PMCID ou DOI para o artigo com PMID: {article_ids.get('pmid')}")

        return None

    async def run_research_cycle(self) -> None:
        """
        Executa um ciclo completo de pesquisa autônoma, usando o fluxo eficiente esearch -> efetch.
        """
        logger.info("\n--- INICIANDO CICLO DE PESQUISA AUTÔNOMA ---")
        if not Entrez:
            logger.critical("Módulo Bio.Entrez não está configurado. O ciclo de pesquisa não pode continuar.")
            return

        research_config = config._config.get('research_agent', {})
        topics: List[str] = research_config.get('topics_of_interest', [])
        max_docs_per_topic: int = research_config.get('max_articles_per_topic', 5)

        if not topics:
            logger.warning("Nenhum tópico de interesse configurado para o ResearchAgent. Ciclo encerrado.")
            return

        for topic in topics:
            logger.info(f"\n[Pesquisando] Tema: '{topic}'")
            try:
                query = f'({topic}) AND (("randomized controlled trial"[Publication Type]) OR ("meta-analysis"[Publication Type]) OR ("guideline"[Publication Type]) OR ("systematic review"[Publication Type]))'
                logger.debug(f"Executando esearch no PubMed: {query}")
                
                esearch_handle = Entrez.esearch(db="pubmed", term=query, retmax=max_docs_per_topic, sort="relevance")
                esearch_record = Entrez.read(esearch_handle)
                esearch_handle.close()
                pmid_list = esearch_record["IdList"]

                if not pmid_list:
                    logger.info(f"Nenhum artigo novo encontrado via esearch para o tema '{topic}'.")
                    continue
                
                logger.info(f"Encontrados {len(pmid_list)} PMIDs para '{topic}'. Buscando detalhes via efetch...")

                efetch_handle = Entrez.efetch(db="pubmed", id=pmid_list, rettype="xml", retmode="xml")
                articles_xml_root = ET.parse(efetch_handle).getroot()
                efetch_handle.close()

                for i, article_xml in enumerate(articles_xml_root.findall(".//PubmedArticle")):
                    logger.info(f"  [Analisando] Artigo {i+1}/{len(pmid_list)} para '{topic}'...")
                    
                    article_data = self._extract_data_from_xml_article(article_xml)
                    pmid = article_data.get("pmid", "N/A")

                    try:
                        llm_response_messages = self.analysis_prompt.format_prompt(
                            topics=", ".join(topics),
                            title=article_data.get('title'),
                            abstract=article_data.get('abstract'),
                            format_instructions=self.analysis_parser.get_format_instructions()
                        ).to_messages()

                        llm_response = await config.throttled_google_acall(self.analyzer_llm, llm_response_messages)
                        llm_response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

                        try:
                            analysis: ArticleAnalysis = self.analysis_parser.parse(llm_response_content)
                        except OutputParserException as e_parse:
                            logger.warning(f"   Falha no parsing Pydantic da análise do LLM. Tentando corrigir... Erro: {e_parse}")
                            analysis: ArticleAnalysis = self.output_fixing_parser.parse(llm_response_content)

                        logger.debug(f"   Análise do LLM (PMID {pmid}): Relevante={analysis.is_relevant}, Resumo='{analysis.summary_pt[:50]}...'")

                        if analysis.is_relevant:
                            logger.info(f"  -> Relevante (PMID: {pmid}): {analysis.reasoning[:100]}...")
                            
                            final_pdf_url = await self._attempt_pdf_extraction(article_data)

                            if final_pdf_url:
                                logger.info(f"   URL de PDF/Artigo encontrada: {final_pdf_url}. Tentando download e ingestão.")
                                self.download_and_ingest(
                                    final_pdf_url,
                                    preferred_filename_base=f"pubmed_{pmid}"
                                )
                            else:
                                logger.warning(f"  -> AVISO: Artigo (PMID: {pmid}) relevante, mas URL do PDF não pôde ser extraída.")
                        else:
                            logger.info(f"  -> Não relevante (PMID: {pmid}): {analysis.reasoning[:100]}...")

                    except Exception as e_analise_artigo:
                        logger.error(f"Erro ao analisar o artigo (PMID: {pmid}): {e_analise_artigo}", exc_info=True)

            except Exception as e_pesquisa_topico:
                logger.error(f"Erro geral ao pesquisar o tema '{topic}': {e_pesquisa_topico}", exc_info=True)
            finally:
                time.sleep(0.5)

        logger.info("\n--- CICLO DE PESQUISA CONCLUÍDO ---")

    def download_and_ingest(self, url: str, preferred_filename_base: str = "article") -> None:
        """
        Baixa um arquivo de uma URL e o ingere na base de conhecimento.
        Tenta determinar se a URL é um PDF direto ou uma página HTML que contém um PDF.
        """
        download_dir = os.path.join("knowledge_sources", "downloads_research_worker")
        os.makedirs(download_dir, exist_ok=True)

        is_direct_pdf_link = url.lower().endswith(".pdf")
        actual_pdf_url_to_download = url

        if not is_direct_pdf_link:
            logger.info(f"URL '{url}' não é um link PDF direto. Tentando encontrar PDF na página HTML...")
            pdf_from_page = self._get_pdf_url_from_html_page(url)
            if pdf_from_page:
                actual_pdf_url_to_download = pdf_from_page
                logger.info(f"PDF encontrado na página HTML: {actual_pdf_url_to_download}")
            else:
                logger.warning(f"Não foi possível encontrar um link PDF na página HTML: {url}. Download cancelado.")
                return

        parsed_url_for_filename = urlparse(actual_pdf_url_to_download)
        url_path_basename = os.path.basename(parsed_url_for_filename.path) if parsed_url_for_filename.path else None
        base_name_to_use = url_path_basename if url_path_basename and '.' in url_path_basename else preferred_filename_base
        clean_base = re.sub(r'[^\w\.\-]', '_', base_name_to_use)
        base, ext = os.path.splitext(clean_base)
        base = base[:50]
        if not ext or ext.lower() not in ['.pdf', '.txt']:
            ext = ".pdf"
        filename = f"{base}_{hashlib.sha1(actual_pdf_url_to_download.encode()).hexdigest()[:8]}{ext}"
        file_path = os.path.join(download_dir, filename)

        ingestion_result_str = "Falha no download"
        try:
            logger.info(f"  [Baixando] Artigo de {actual_pdf_url_to_download} para {file_path}")
            req = Request(actual_pdf_url_to_download, headers={'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'})
            with urlopen(req, timeout=30) as response, open(file_path, 'wb') as out_file:
                content_type = response.info().get('Content-Type', '').lower()
                if not ('application/pdf' in content_type or file_path.lower().endswith(".pdf")):
                    logger.warning(f"  -> AVISO: Conteúdo de {actual_pdf_url_to_download} pode não ser PDF (Content-Type: {content_type}). Arquivo salvo como {file_path}")
                out_file.write(response.read())
            logger.info(f"  Download completo: {file_path}")

            if kb_manager:
                ingestion_result_str = kb_manager.ingest_new_document(file_path=file_path)
                logger.info(f"  [Ingestão] Resultado para '{filename}': {ingestion_result_str}")
            else:
                ingestion_result_str = "Falha: kb_manager não está disponível."
                logger.error(ingestion_result_str)


        except HTTPError as e_http:
            logger.error(f"  -> ERRO HTTP {e_http.code} ao baixar de {actual_pdf_url_to_download}: {e_http.reason}")
            ingestion_result_str = f"Erro HTTP {e_http.code}"
        except Exception as e_download:
            logger.error(f"  -> ERRO no download/ingestão de {actual_pdf_url_to_download}: {e_download}", exc_info=True)
            ingestion_result_str = f"Erro: {e_download}"
        finally:
            if os.path.exists(file_path) and "sucesso" not in ingestion_result_str.lower():
                logger.warning(f"  Ingestão de '{filename}' não bem-sucedida ('{ingestion_result_str}'). Removendo: {file_path}")
                try:
                    os.remove(file_path)
                except OSError as e_remove:
                    logger.error(f"  Falha ao remover '{file_path}': {e_remove}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s [%(levelname)s] - %(module)s.%(funcName)s: %(message)s'
    )
    logger.info("Iniciando Research Worker...")
    
    if kb_manager is None:
        logger.critical("KnowledgeBaseManager não pôde ser inicializado devido a erros anteriores. Encerrando o Research Worker.")
        exit(1)

    try:
        agent = ResearchAgent()
    except SystemExit:
        logger.critical("Não foi possível inicializar o ResearchAgent. Encerrando o worker.")
        exit(1)

    research_agent_config = config._config.get('research_agent', {})
    run_interval_hours = research_agent_config.get('run_interval_hours', 24)

    def run_async_job():
        import asyncio
        try:
            asyncio.run(agent.run_research_cycle())
        except Exception as e:
            logger.error(f"Erro fatal ao executar job assíncrono agendado: {e}", exc_info=True)

    schedule.every(run_interval_hours).hours.do(run_async_job)

    logger.info("Executando o primeiro ciclo de pesquisa imediatamente (async)...")
    try:
        import asyncio
        asyncio.run(agent.run_research_cycle())
    except Exception as e_first_run:
        logger.error(f"Erro durante a primeira execução do ciclo de pesquisa: {e_first_run}", exc_info=True)

    logger.info(f"Research Worker iniciado. Próxima execução agendada em {run_interval_hours} horas.")
    while True:
        schedule.run_pending()
        time.sleep(60)
