# research_worker.py
import schedule
import time
import os
import hashlib
import re # Importado re para regex
import logging # Importado logging
from urllib.request import urlretrieve, HTTPError # Importado HTTPError
from urllib.parse import urlparse # Importado para parsear URL
from dotenv import load_dotenv

load_dotenv()

from langchain_community.tools.pubmed.tool import PubMedQueryRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from config_loader import config
from kb_manager import kb_manager

class ArticleAnalysis(BaseModel):
    is_relevant: bool = Field(description="True se o artigo for clinicamente relevante.")
    summary_pt: str = Field(description="Resumo do artigo em português.")
    reasoning: str = Field(description="Justificativa da relevância.")
    pdf_url: str = Field(description="URL do PDF ou 'N/A'.")

class ResearchAgent:
    def __init__(self):
        self.pubmed_tool = PubMedQueryRun()
        self.analyzer_llm = config.get_llm("critique_agent")
        self.analysis_parser = PydanticOutputParser(pydantic_object=ArticleAnalysis)
        self.analysis_prompt = ChatPromptTemplate.from_template(
            "Analise o abstract a seguir sobre os temas {topics} e determine sua relevância para nossa base de conhecimento sobre obesidade e doenças metabólicas. Forneça um resumo em português e a URL do PDF se disponível.\n\nAbstract:\n{abstract}\n\n{format_instructions}",
            partial_variables={"format_instructions": self.analysis_parser.get_format_instructions()}
        )
        self.analyzer_chain = self.analysis_prompt | self.analyzer_llm | self.analysis_parser

    def _get_pdf_url_from_pubmed_entry(self, pubmed_entry: str) -> str:
        # Tenta encontrar URLs que parecem ser de PDFs de forma mais genérica
        # Prioriza URLs que contenham 'pdf', mas também captura outras URLs diretas.
        # Regex para encontrar URLs HTTP/HTTPS
        # Este regex é uma simplificação e pode não cobrir todos os casos de URLs válidas.
        url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')

        potential_urls = url_pattern.findall(pubmed_entry)

        pdf_urls = []
        other_urls = []

        for url in potential_urls:
            # Remove possíveis caracteres de pontuação no final da URL
            url = url.strip('.,)')
            if '.pdf' in url.lower() or 'application/pdf' in pubmed_entry.lower():
                pdf_urls.append(url)
            # Adiciona uma verificação para links diretos para alguns repositórios comuns
            elif any(domain in url for domain in ["ncbi.nlm.nih.gov/pmc/articles", "europepmc.org/articles"]):
                 # Tenta encontrar links de texto completo dentro dessas páginas (simplificado)
                if "pdf" in pubmed_entry.lower() or "full text" in pubmed_entry.lower(): # Verifica se há menção a PDF no contexto
                    other_urls.append(url) # Adiciona como uma URL genérica se não for claramente um PDF direto
            elif "doi.org" in url and "pdf" not in url.lower(): # Evita URLs DOI que não são PDFs diretos
                continue
            else:
                other_urls.append(url)

        if pdf_urls:
            logging.info(f"URLs de PDF encontradas na entrada do PubMed: {pdf_urls}")
            return pdf_urls[0] # Retorna a primeira URL de PDF encontrada

        if other_urls:
            logging.info(f"Outras URLs encontradas na entrada do PubMed (tentativa com a primeira): {other_urls}")
            # Poderia tentar verificar o Content-Type aqui se fosse mais sofisticado,
            # mas por agora, retorna a primeira URL genérica se nenhuma de PDF for clara.
            return other_urls[0]

        logging.warning("Nenhuma URL de PDF ou link de artigo promissor encontrado na entrada do PubMed.")
        return "N/A"

    def run_research_cycle(self):
        logging.info("\n--- INICIANDO CICLO DE PESQUISA AUTÔNOMA ---")
        research_config = config._config.get('research_agent', {})
        topics = research_config.get('topics_of_interest', [])
        max_docs = research_config.get('max_articles_per_topic', 3)

        for topic in topics:
            logging.info(f"\n[Pesquisando] Tema: '{topic}'")
            try:
                query = f'({topic}) AND (("randomized controlled trial"[Publication Type]) OR ("meta-analysis"[Publication Type]) OR ("guideline"[Publication Type]))'
                results = self.pubmed_tool.run(query) # Considerar adicionar try-except aqui se a ferramenta puder falhar
                articles = ["Published:" + article for article in results.strip().split('Published:') if article.strip()]
                logging.info(f"Encontrados {len(articles)} artigos para o tema '{topic}'.")

                for i, article_text in enumerate(articles[:max_docs]):
                    logging.info(f"  [Analisando] Artigo {i+1}/{len(articles[:max_docs])} para '{topic}'...")
                    try:
                        analysis = self.analyzer_chain.invoke({"topics": ", ".join(topics), "abstract": article_text})
                        if analysis.is_relevant:
                            logging.info(f"  -> Relevante: {analysis.reasoning}")
                            pdf_url = self._get_pdf_url_from_pubmed_entry(article_text)
                            if pdf_url != "N/A":
                                self.download_and_ingest(pdf_url, preferred_filename_base=f"pubmed_{topic.replace(' ','_')}_{i+1}")
                            else:
                                logging.warning("  -> AVISO: Artigo relevante, mas URL do PDF não encontrada ou extraída.")
                        else:
                            logging.info(f"  -> Não relevante: {analysis.reasoning}")
                    except Exception as e_analise:
                        logging.error(f"Erro ao analisar o artigo {i+1} para o tema '{topic}': {e_analise}", exc_info=True)
            except Exception as e_pesquisa:
                logging.error(f"Erro ao pesquisar o tema '{topic}': {e_pesquisa}", exc_info=True)
        logging.info("\n--- CICLO DE PESQUISA CONCLUÍDO ---")

    def download_and_ingest(self, url: str, preferred_filename_base: str = "article"):
        try:
            download_dir = os.path.join("knowledge_sources", "downloads")
            os.makedirs(download_dir, exist_ok=True)

            # Tenta extrair um nome de arquivo da URL, senão usa um hash ou o nome base preferido
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            url_filename = path_parts[-1] if path_parts[-1] else None

            if url_filename and '.' in url_filename: # Se houver um nome de arquivo com extensão na URL
                 # Limpa caracteres problemáticos do nome do arquivo da URL
                clean_url_filename = re.sub(r'[^\w\.\-]', '_', url_filename)
                base, ext = os.path.splitext(clean_url_filename)
                base = base[:50] # Limita o tamanho do nome base
                filename = f"{base}{ext}"
            else: # Senão, constrói a partir do preferred_filename_base ou hash
                clean_base = re.sub(r'[^\w\.\-]', '_', preferred_filename_base)
                clean_base = clean_base[:50]
                filename = f"{clean_base}_{hashlib.sha1(url.encode()).hexdigest()[:10]}.pdf"

            if not filename.lower().endswith(('.pdf', '.txt')): # Garante que termine com .pdf se não tiver extensão válida
                 if '.pdf' not in filename.lower(): # Evita adicionar .pdf se já tiver outra extensão como .html
                    filename += ".pdf"

            file_path = os.path.join(download_dir, filename)
            
            logging.info(f"  [Baixando] Artigo de {url} para {file_path}")
            # Adicionar cabeçalhos para simular um navegador pode ajudar com alguns servidores
            # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            # req = urllib.request.Request(url, headers=headers)
            # with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
            #     shutil.copyfileobj(response, out_file)
            urlretrieve(url, file_path) # Mantendo urlretrieve por simplicidade por enquanto

            # Verificação básica do tipo de arquivo após download (pela extensão)
            if not file_path.lower().endswith(".pdf"):
                # Tentar verificar o magic number seria mais robusto aqui
                logging.warning(f"  -> AVISO: Arquivo baixado '{file_path}' não parece ser um PDF pela extensão.")
                # Decide se quer prosseguir ou não. Por ora, vamos prosseguir com o aviso.
                # os.remove(file_path) # Opção: remover se não for PDF
                # return

            result = kb_manager.ingest_new_document(file_path)
            logging.info(f"  [Ingestão] Resultado para '{filename}': {result}")

        except HTTPError as e:
            logging.error(f"  -> ERRO HTTP: Falha ao baixar de {url}. Código: {e.code}. Razão: {e.reason}")
        except Exception as e:
            logging.error(f"  -> ERRO: Falha no processo de download ou ingestão de {url}. Erro: {e}", exc_info=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    agent = ResearchAgent()
    run_interval = config._config.get('research_agent', {}).get('run_interval_hours', 24)
    print(f"Agendando a execução do ciclo de pesquisa a cada {run_interval} horas.")
    schedule.every(run_interval).hours.do(agent.run_research_cycle)
    
    print("Executando o primeiro ciclo de pesquisa imediatamente...")
    agent.run_research_cycle()

    while True:
        schedule.run_pending()
        time.sleep(60)
