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
from langchain_community.tools.pubmed.tool import PubMedQueryRun # Usado para busca inicial
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser, OutputParserException
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
        self.pubmed_tool = PubMedQueryRun(email=ENTREZ_EMAIL)
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
            "Você é um assistente de pesquisa especializado em medicina metabólica. Analise o seguinte abstract de um artigo científico em relação aos tópicos de interesse: {topics}. "
            "Determine se o artigo possui alta relevância clínica e apresenta evidências fortes (ex: ensaios clínicos randomizados, meta-análises, diretrizes de grandes sociedades). "
            "Forneça um resumo conciso em português (3-4 frases).\n\n"
            "Abstract e Metadados do Artigo:\n{abstract}\n\n{format_instructions}",
            partial_variables={"format_instructions": self.analysis_parser.get_format_instructions()}
        )
        # self.analyzer_chain = self.analysis_prompt | self.analyzer_llm # Parser será aplicado depois

    def _extract_ids_from_pubmed_text(self, pubmed_entry_text: str) -> Dict[str, Optional[str]]:
        """Extrai PMID, DOI e PMCID do texto de entrada do PubMed se disponíveis."""
        ids: Dict[str, Optional[str]] = {"pmid": None, "doi": None, "pmcid": None}

        pmid_match = re.search(r"PMID:\s*(\d+)", pubmed_entry_text, re.IGNORECASE)
        if pmid_match:
            ids["pmid"] = pmid_match.group(1)

        doi_match = re.search(r"DOI:\s*([^\s]+)", pubmed_entry_text, re.IGNORECASE)
        if doi_match:
            ids["doi"] = doi_match.group(1).strip('.') # Remove ponto final se houver

        pmcid_match = re.search(r"PMCID:\s*(PMC\d+)", pubmed_entry_text, re.IGNORECASE)
        if pmcid_match:
            ids["pmcid"] = pmcid_match.group(1)

        logger.debug(f"IDs extraídos do texto PubMed: {ids}")
        return ids

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
                # Tentar buscar o PDF diretamente da página PMC é complexo aqui.
                # Por ora, vamos assumir que se houver um link PMC, vale a pena tentar.
                # Uma melhoria seria buscar o link do PDF dentro da página PMC.
                # Para simplificar, vamos tentar construir um link de PDF comum do PMC.
                # Ex: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12345/pdf/algum_nome.pdf
                # Esta é uma heurística e pode não funcionar sempre.
                # Uma abordagem mais robusta seria usar a API do PMC para obter o link do PDF.
                # Por ora, apenas retornar o link da página do artigo PMC.
                # O LLM ou outra lógica pode tentar encontrar o PDF a partir daqui.
                # Ou, melhor, podemos tentar uma URL de PDF direta se o XML fornecer.

                # Tenta encontrar um link de PDF direto no XML (menos comum, mas possível)
                for link in root.findall(".//ArticleLink[contains(@ProviderId, 'PubMed Central')]/Url"): # Heurística
                     if link.text and link.text.lower().endswith(".pdf"):
                        logger.info(f"Link PDF direto encontrado no XML do Entrez (via ArticleLink PMC): {link.text}")
                        return link.text

                # Tenta encontrar links na seção 'OtherLink' que podem ser PDFs
                for other_link in root.findall(".//OtherAbstract/AbstractText[@Label='TEXTCOMPLETELINK']/OtherLink"):
                    if other_link.text and other_link.text.lower().endswith(".pdf"):
                        logger.info(f"Link PDF direto encontrado no XML do Entrez (via OtherLink): {other_link.text}")
                        return other_link.text

                # Se não encontrar PDF direto, retorna o link da página do artigo PMC
                logger.info(f"Retornando link da página do artigo PMC: {pmc_url} (PDF direto não encontrado no XML)")
                return pmc_url # O download_and_ingest precisará de lógica para lidar com isso

        # Tenta encontrar DOI para resolver externamente se não houver link PMC
        doi_element = root.find(".//ArticleId[@IdType='doi']")
        if doi_element is not None and doi_element.text:
            doi = doi_element.text
            doi_url = f"https://doi.org/{doi}"
            logger.info(f"DOI encontrado no XML: {doi}. URL: {doi_url}. Este DOI pode ser usado para buscar PDF.")
            # Retornar a URL do DOI pode ser uma opção se outras falharem.
            # A função de download precisaria então tentar resolver o DOI e encontrar o PDF.
            # Por enquanto, priorizamos PMC. Se não houver PMC, esta é uma alternativa.
            # return doi_url

        logger.debug("Nenhuma URL de PDF ou link PMC promissor encontrado no XML do Entrez.")
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
                    # Heurísticas comuns para encontrar links de PDF
                    # 1. Links <a> com href terminando em .pdf
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        if href.lower().endswith(".pdf"):
                            # Garante que a URL seja absoluta
                            pdf_link = urljoin(page_url, href)
                            logger.info(f"Link PDF encontrado em HTML ({page_url}): {pdf_link}")
                            return pdf_link
                    # 2. Links <a> contendo texto como "PDF", "Full Text PDF" (case-insensitive)
                    for a_tag in soup.find_all('a', href=True, string=re.compile(r'pdf|full text', re.I)):
                        href = a_tag['href']
                        # Alguns sites usam javascript: ou botões, o que é mais difícil.
                        # Focar em hrefs diretos.
                        if href and not href.lower().startswith('javascript:'):
                             pdf_link = urljoin(page_url, href)
                             logger.info(f"Link PDF (por texto) encontrado em HTML ({page_url}): {pdf_link}")
                             # Não necessariamente é um PDF direto, mas é um candidato
                             return pdf_link
                    logger.debug(f"Nenhum link PDF óbvio encontrado na página HTML: {page_url}")
                else:
                    logger.warning(f"Falha ao buscar página HTML {page_url}, status: {response.status}")
        except Exception as e:
            logger.error(f"Erro ao tentar buscar/parsear HTML de {page_url}: {e}", exc_info=True)
        return None

    async def _attempt_pdf_extraction(self, pubmed_entry_text: str, article_ids: Dict[str, Optional[str]]) -> Optional[str]:
        """Orquestra as tentativas de extração de URL de PDF."""
        # 1. Tenta regex no texto original (rápido, mas menos confiável)
        url_from_regex = self._get_pdf_url_from_pubmed_entry(pubmed_entry_text)
        if url_from_regex and url_from_regex.lower().endswith(".pdf"):
            logger.info(f"PDF encontrado via regex direto no abstract: {url_from_regex}")
            return url_from_regex

        # 2. Tenta via Entrez XML se tiver PMID
        if article_ids.get("pmid") and Entrez:
            xml_data = self._fetch_pubmed_xml(article_ids["pmid"])
            if xml_data:
                url_from_xml = self._extract_pdf_url_from_entrez_xml(xml_data)
                if url_from_xml:
                    if url_from_xml.lower().endswith(".pdf"):
                        logger.info(f"PDF encontrado via Entrez XML (direto): {url_from_xml}")
                        return url_from_xml
                    # Se for um link PMC ou DOI, pode precisar de mais um passo
                    if "ncbi.nlm.nih.gov/pmc/articles/" in url_from_xml or "doi.org/" in url_from_xml:
                        logger.info(f"Link para página de artigo (PMC/DOI) encontrado via XML: {url_from_xml}. Tentando encontrar PDF nessa página.")
                        pdf_from_page = self._get_pdf_url_from_html_page(url_from_xml)
                        if pdf_from_page: return pdf_from_page

        # 3. Se um DOI foi extraído do texto inicial e não foi processado via XML
        if article_ids.get("doi") and not (article_ids.get("pmid") and xml_data) : # Evita reprocessar DOI se já veio do XML
            doi_url = f"https://doi.org/{article_ids['doi']}"
            logger.info(f"Tentando encontrar PDF a partir de DOI extraído do texto: {doi_url}")
            pdf_from_doi_page = self._get_pdf_url_from_html_page(doi_url)
            if pdf_from_doi_page: return pdf_from_doi_page

        # 4. Retorna a URL do regex (mesmo que não seja .pdf direto) se foi a única coisa encontrada
        if url_from_regex:
            logger.info(f"Retornando URL de fallback do regex (pode não ser PDF direto): {url_from_regex}")
            return url_from_regex

        logger.warning(f"Não foi possível extrair uma URL de PDF confiável para o artigo com IDs: {article_ids}")
        return None

    async def run_research_cycle(self) -> None:
        """
        Executa um ciclo completo de pesquisa autônoma.
        """
        logger.info("\n--- INICIANDO CICLO DE PESQUISA AUTÔNOMA ---")
        # ... (código de configuração de topics e max_docs_per_topic) ...
        research_config = config._config.get('research_agent', {})
        topics: List[str] = research_config.get('topics_of_interest', [])
        max_docs_per_topic: int = research_config.get('max_articles_per_topic', 3)

        if not topics:
            logger.warning("Nenhum tópico de interesse configurado para o ResearchAgent. Ciclo encerrado.")
            return

        for topic in topics:
            logger.info(f"\n[Pesquisando] Tema: '{topic}'")
            try:
                query = f'({topic}) AND (("randomized controlled trial"[Publication Type]) OR ("meta-analysis"[Publication Type]) OR ("guideline"[Publication Type]) OR ("systematic review"[Publication Type]))'
                logger.debug(f"Executando query no PubMed: {query}")
                try:
                    pubmed_results_str: str = self.pubmed_tool.run(query)
                except Exception as e_pubmed_tool:
                    logger.error(f"Falha ao executar PubMedQueryRun para o tema '{topic}': {e_pubmed_tool}", exc_info=True)
                    continue

                raw_articles = pubmed_results_str.strip().split('Published:')
                articles_texts = ["Published:" + article_text.strip() for article_text in raw_articles if article_text.strip()]
                logger.info(f"Encontrados {len(articles_texts)} resultados brutos para o tema '{topic}'.")

                for i, article_text_content in enumerate(articles_texts[:max_docs_per_topic]):
                    logger.info(f"  [Analisando] Artigo {i+1}/{len(articles_texts[:max_docs_per_topic])} para '{topic}'...")
                    article_ids = self._extract_ids_from_pubmed_text(article_text_content)
                    logger.debug(f"   IDs para o artigo atual: {article_ids}")

                    try:
                        # LLM para análise de relevância e resumo
                        # O prompt foi atualizado para não pedir mais a URL do PDF ao LLM
                        llm_response_messages = self.analysis_prompt.format_prompt(
                                topics=", ".join(topics),
                                abstract=article_text_content, # Passa o texto completo do resultado do PubMed
                                format_instructions=self.analysis_parser.get_format_instructions()
                            ).to_messages()

                        llm_response = await config.throttled_google_acall(self.analyzer_llm, {"input": llm_response_messages} if hasattr(self.analyzer_llm, 'invoke') else llm_response_messages)
                        llm_response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)


                        try:
                            analysis: ArticleAnalysis = self.analysis_parser.parse(llm_response_content)
                        except OutputParserException:
                            logger.warning("   Falha no parsing Pydantic da análise do LLM. Tentando corrigir...")
                            analysis: ArticleAnalysis = self.output_fixing_parser.parse(llm_response_content)

                        logger.debug(f"   Análise do LLM: Relevante={analysis.is_relevant}, Resumo='{analysis.summary_pt[:50]}...'")

                        if analysis.is_relevant:
                            logger.info(f"  -> Relevante: {analysis.reasoning[:100]}...")

                            # Nova lógica de extração de PDF
                            final_pdf_url = await self._attempt_pdf_extraction(article_text_content, article_ids)

                            if final_pdf_url:
                                logger.info(f"   URL de PDF/Artigo encontrada: {final_pdf_url}. Tentando download e ingestão.")
                                self.download_and_ingest(
                                    final_pdf_url,
                                    preferred_filename_base=f"pubmed_{article_ids.get('pmid', topic.replace(' ','_'))}_{i+1}"
                                )
                            else:
                                logger.warning(f"  -> AVISO: Artigo (PMID: {article_ids.get('pmid','N/A')}) relevante, mas URL do PDF não pôde ser extraída.")
                        else:
                            logger.info(f"  -> Não relevante: {analysis.reasoning[:100]}...")

                    except Exception as e_analise_artigo:
                        logger.error(f"Erro ao analisar o artigo (PMID: {article_ids.get('pmid','N/A')}): {e_analise_artigo}", exc_info=True)

            except Exception as e_pesquisa_topico:
                logger.error(f"Erro geral ao pesquisar o tema '{topic}': {e_pesquisa_topico}", exc_info=True)

        logger.info("\n--- CICLO DE PESQUISA CONCLUÍDO ---")

    def download_and_ingest(self, url: str, preferred_filename_base: str = "article") -> None:
        """
        Baixa um arquivo de uma URL e o ingere na base de conhecimento.
        Tenta determinar se a URL é um PDF direto ou uma página HTML que contém um PDF.
        """
        download_dir = os.path.join("knowledge_sources", "downloads_research_worker")
        os.makedirs(download_dir, exist_ok=True)

        # Verifica se a URL já é um PDF direto
        is_direct_pdf_link = url.lower().endswith(".pdf")
        actual_pdf_url_to_download = url

        if not is_direct_pdf_link:
            logger.info(f"URL '{url}' não é um link PDF direto. Tentando encontrar PDF na página HTML...")
            pdf_from_page = self._get_pdf_url_from_html_page(url)
            if pdf_from_page:
                actual_pdf_url_to_download = pdf_from_page
                logger.info(f"PDF encontrado na página HTML: {actual_pdf_url_to_download}")
            else:
                logger.warning(f"Não foi possível encontrar um link PDF na página HTML: {url}. Tentando baixar a URL original como fallback (pode não ser PDF).")
                # Se não encontrar PDF na página, pode tentar baixar a URL original,
                # mas é menos provável que seja um PDF se não terminar com .pdf.
                # Ou poderia simplesmente desistir aqui. Por ora, tenta a URL original.

        # Criação do nome do arquivo (similar à lógica anterior)
        parsed_url_for_filename = urlparse(actual_pdf_url_to_download)
        url_path_basename = os.path.basename(parsed_url_for_filename.path) if parsed_url_for_filename.path else None
        base_name_to_use = url_path_basename if url_path_basename and '.' in url_path_basename else preferred_filename_base
        clean_base = re.sub(r'[^\w\.\-]', '_', base_name_to_use)
        base, ext = os.path.splitext(clean_base)
        base = base[:50]
        if not ext or ext.lower() not in ['.pdf', '.txt']: # Garante extensão .pdf se não for txt
            ext = ".pdf"
        filename = f"{base}_{hashlib.sha1(actual_pdf_url_to_download.encode()).hexdigest()[:8]}{ext}"
        file_path = os.path.join(download_dir, filename)

        ingestion_result_str = "Falha no download" # Default
        try:
            logger.info(f"  [Baixando] Artigo de {actual_pdf_url_to_download} para {file_path}")
            req = Request(actual_pdf_url_to_download, headers={'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}) # User-Agent genérico
            with urlopen(req, timeout=30) as response, open(file_path, 'wb') as out_file:
                content_type = response.info().get('Content-Type', '').lower()
                if not ('application/pdf' in content_type or file_path.lower().endswith(".pdf")):
                    logger.warning(f"  -> AVISO: Conteúdo de {actual_pdf_url_to_download} pode não ser PDF (Content-Type: {content_type}). Arquivo salvo como {file_path}")
                out_file.write(response.read())
            logger.info(f"  Download completo: {file_path}")

            ingestion_result_str = kb_manager.ingest_new_document(file_path=file_path)
            logger.info(f"  [Ingestão] Resultado para '{filename}': {ingestion_result_str}")

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
        level=logging.DEBUG, # DEBUG para ver mais detalhes do research_worker
        format='%(asctime)s - %(name)s [%(levelname)s] - %(module)s.%(funcName)s: %(message)s'
    )
    logger.info("Iniciando Research Worker...")
    
    # ... (resto do __main__ como antes) ...
    try:
        agent = ResearchAgent()
    except SystemExit:
        logger.critical("Não foi possível inicializar o ResearchAgent. Encerrando o worker.")
        exit(1) # Sai se o agente não puder ser inicializado

    research_agent_config = config._config.get('research_agent', {})
    run_interval_hours = research_agent_config.get('run_interval_hours', 24)

    logger.info(f"Agendando a execução do ciclo de pesquisa a cada {run_interval_hours} horas.")
    schedule.every(run_interval_hours).hours.do(agent.run_research_cycle)

    logger.info("Executando o primeiro ciclo de pesquisa imediatamente...")
    try:
        # Para rodar async run_research_cycle em um contexto síncrono como o schedule
        # ou a primeira execução, precisamos de asyncio.run ou similar se houver chamadas async dentro.
        # Como run_research_cycle foi mantido síncrono (e chama await config.throttled_google_acall),
        # e config.throttled_google_acall é async, isso vai dar erro.
        # A solução mais simples é tornar run_research_cycle async e usar asyncio.run aqui.
        # Ou, refatorar throttled_google_acall para ter uma versão sync se possível,
        # ou usar um loop de evento para chamadas async.
        # Por ora, vou assumir que o throttled_google_acall pode ser chamado de um contexto sync
        # se o loop de evento estiver rodando (o que não é o caso aqui).
        # A maneira correta seria:
        # import asyncio
        # asyncio.run(agent.run_research_cycle())
        # No entanto, como o schedule não suporta jobs async diretamente,
        # uma solução comum é rodar o schedule em um thread e o loop asyncio em outro,
        # ou usar uma biblioteca de schedule async.
        # Para simplificar MUITO por agora, e dado que o `await` estava dentro de um método síncrono antes,
        # vou remover o `await` da chamada ao `throttled_google_acall` DENTRO do `run_research_cycle`
        # e da chamada ao `analyzer_llm` (que é o `throttled_google_acall`),
        # e torná-los chamadas síncronas se o `config_loader` permitir ou se usarmos `invoke` em vez de `ainvoke`.
        # Esta é uma simplificação que pode precisar ser revista para um asyncio "correto".
        # Revertendo: throttled_google_acall é async. O LLM invoke é async.
        # O run_research_cycle PRECISA ser async.
        # E o __main__ precisa chamar com asyncio.run().
        # O schedule precisaria de um wrapper para chamar uma função async.

        # Wrapper para schedule
        def run_async_job():
            import asyncio
            asyncio.run(agent.run_research_cycle())

        schedule.every(run_interval_hours).hours.do(run_async_job)

        logger.info("Executando o primeiro ciclo de pesquisa imediatamente (async)...")
        import asyncio
        asyncio.run(agent.run_research_cycle()) # Executa o primeiro ciclo

    except Exception as e_first_run:
        logger.error(f"Erro durante a primeira execução do ciclo de pesquisa: {e_first_run}", exc_info=True)

    logger.info("Research Worker iniciado e aguardando execuções agendadas...")
    while True:
        schedule.run_pending()
        time.sleep(60)
