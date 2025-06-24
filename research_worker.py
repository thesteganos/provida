# research_worker.py
import schedule
import time
import os
import hashlib
from urllib.request import urlretrieve
from dotenv import load_dotenv

# Carrega o ambiente antes de tudo
load_dotenv()

# --- IMPORTAÇÃO CORRIGIDA ---
from langchain_community.tools.pubmed.tool import PubMedQueryRun
# -----------------------------

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

from config_loader import config
from kb_manager import kb_manager

# --- Modelos Pydantic para Saídas Estruturadas ---
class ArticleAnalysis(BaseModel):
    is_relevant: bool = Field(description="True se o artigo for clinicamente relevante para os temas de interesse.")
    summary_pt: str = Field(description="Um resumo conciso do artigo, traduzido para o português.")
    reasoning: str = Field(description="Justificativa sobre a relevância do artigo.")
    pdf_url: str = Field(description="URL direta para o PDF, se disponível, caso contrário 'N/A'.")

# --- Lógica do Agente ---
class ResearchAgent:
    def __init__(self):
        self.pubmed_tool = PubMedQueryRun()
        self.analyzer_llm = config.get_llm("critique_agent") # Reutilizando um modelo rápido
        self.analysis_parser = PydanticOutputParser(pydantic_object=ArticleAnalysis)
        self.analysis_prompt = ChatPromptTemplate.from_template(
            """Você é um assistente de pesquisa médica. Sua tarefa é analisar o resumo (abstract) de um artigo científico para decidir se ele é relevante para ser adicionado à nossa base de conhecimento sobre obesidade e doenças metabólicas.

            **Temas de Interesse:** {topics}

            **Abstract do Artigo:**
            {abstract}

            **Sua Análise:**
            1. O artigo é diretamente relevante para o tratamento, diagnóstico ou fisiopatologia da obesidade, diabetes, ou síndrome metabólica?
            2. Forneça um resumo conciso e informativo do abstract em **português**.
            3. Justifique brevemente por que este artigo deve ou não ser incluído.
            4. Se houver um link para o PDF, extraia-o.

            Responda usando o seguinte formato JSON:
            {format_instructions}
            """,
            partial_variables={"format_instructions": self.analysis_parser.get_format_instructions()}
        )
        self.analyzer_chain = self.analysis_prompt | self.analyzer_llm | self.analysis_parser

    def _get_pdf_url_from_pubmed_entry(self, pubmed_entry: str) -> str:
        lines = pubmed_entry.split('\n')
        for line in lines:
            if "pdf" in line.lower() and "http" in line:
                url_start = line.find("http")
                if url_start != -1:
                    url = line[url_start:]
                    return url.split(' ')[0].strip()
        return "N/A"

    def run_research_cycle(self):
        """Executa um ciclo completo de pesquisa, análise e ingestão."""
        print("\n--- INICIANDO NOVO CICLO DE PESQUISA AUTÔNOMA ---")
        research_config = config._config.get('research_agent', {})
        topics = research_config.get('topics_of_interest', [])
        max_docs = research_config.get('max_articles_per_topic', 3)

        for topic in topics:
            print(f"\n[Pesquisando] Tema: '{topic}'")
            try:
                search_query = f'({topic}) AND (("randomized controlled trial"[Publication Type]) OR ("meta-analysis"[Publication Type]) OR ("guideline"[Publication Type]))'
                search_results = self.pubmed_tool.run(search_query)
                
                articles = search_results.strip().split('Published:')
                articles = ["Published:" + article for article in articles if article.strip()]
                
                print(f"Encontrados {len(articles)} artigos para o tema.")

                for i, article_text in enumerate(articles[:max_docs]):
                    print(f"  [Analisando] Artigo {i+1}/{len(articles[:max_docs])}...")
                    
                    analysis = self.analyzer_chain.invoke({
                        "topics": ", ".join(topics),
                        "abstract": article_text
                    })

                    if analysis.is_relevant:
                        print(f"  -> Relevante: {analysis.reasoning}")
                        pdf_url = self._get_pdf_url_from_pubmed_entry(article_text)
                        if pdf_url != "N/A":
                            self.download_and_ingest(pdf_url)
                        else:
                            print("  -> AVISO: Artigo relevante, mas URL do PDF não encontrada no resumo.")
                    else:
                        print(f"  -> Não relevante: {analysis.reasoning}")

            except Exception as e:
                print(f"Erro ao pesquisar o tema '{topic}': {e}")
        
        print("\n--- CICLO DE PESQUISA CONCLUÍDO ---")

    def download_and_ingest(self, url: str):
        """Baixa um PDF e o envia para ingestão no KB Manager."""
        try:
            download_dir = os.path.join("knowledge_sources", "downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            filename = url.split('/')[-1].split('?')[0] # Limpa parâmetros de URL
            if not filename.endswith('.pdf'):
                filename = f"{hashlib.sha1(url.encode()).hexdigest()}.pdf"
            
            file_path = os.path.join(download_dir, filename)

            print(f"  [Baixando] Artigo de {url} para {file_path}")
            urlretrieve(url, file_path)

            result = kb_manager.ingest_new_document(file_path)
            print(f"  [Ingestão] Resultado: {result}")

        except Exception as e:
            print(f"  -> ERRO: Falha ao baixar ou ingerir de {url}. Erro: {e}")

if __name__ == "__main__":
    agent = ResearchAgent()
    
    run_interval = config._config.get('research_agent', {}).get('run_interval_hours', 24)
    print(f"Agendando a execução do ciclo de pesquisa a cada {run_interval} horas.")
    schedule.every(run_interval).hours.do(agent.run_research_cycle)
    
    # Executa uma vez imediatamente ao iniciar para testes
    print("Executando o primeiro ciclo de pesquisa imediatamente...")
    agent.run_research_cycle()

    while True:
        schedule.run_pending()
        time.sleep(60)
