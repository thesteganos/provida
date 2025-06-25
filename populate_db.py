# populate_db.py
"""
Este script é uma ferramenta de linha de comando para gerenciar a base de dados da aplicação PROVIDA.

Ele oferece funcionalidades para:
1. Resetar o ambiente.
2. Popular o Grafo de Conhecimento Médico com dados básicos.
3. Ingerir documentos PDF locais da base de conhecimento inicial.
"""
import os
import argparse
import logging
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from dotenv import load_dotenv
from reset_environment import reset_neo4j, reset_vectorstore

# MODIFICADO: Importa o kb_manager para a ingestão local
from kb_manager import kb_manager

load_dotenv()
logger = logging.getLogger(__name__)

CYPHER_QUERIES = [
    # Nós
    "MERGE (g:Guideline {name: 'PCDT Sobrepeso e Obesidade'}) ON CREATE SET g.source = 'MS-2024', g.created_at = timestamp() ON MATCH SET g.updated_at = timestamp();",
    "MERGE (c1:Condition {name: 'Obesidade Grau I'}) ON CREATE SET c1.min_imc = 30.0, c1.max_imc = 34.9, c1.created_at = timestamp() ON MATCH SET c1.updated_at = timestamp();",
    "MERGE (c2:Condition {name: 'Diabetes Mellitus Tipo 2'}) ON CREATE SET c2.created_at = timestamp() ON MATCH SET c2.updated_at = timestamp();",
    "MERGE (m1:Medication {name: 'Metformina'}) ON CREATE SET m1.created_at = timestamp() ON MATCH SET m1.updated_at = timestamp();",
    "MERGE (m2:Medication {name: 'Semaglutida'}) ON CREATE SET m2.created_at = timestamp() ON MATCH SET m2.updated_at = timestamp();",
    "MERGE (f1:Food {name: 'Brócolis'}) ON CREATE SET f1.glycemic_index = 15, f1.type = 'vegetal', f1.created_at = timestamp() ON MATCH SET f1.updated_at = timestamp();",
    "MERGE (f2:Food {name: 'Arroz Branco'}) ON CREATE SET f2.glycemic_index = 73, f2.type = 'carboidrato', f2.created_at = timestamp() ON MATCH SET f2.updated_at = timestamp();",

    # Relacionamentos
    "MATCH (g:Guideline {name: 'PCDT Sobrepeso e Obesidade'}), (c:Condition {name: 'Obesidade Grau I'}) MERGE (g)-[r:RECOMMENDS_TREATMENT_FOR]->(c) ON CREATE SET r.created_at = timestamp();",
    "MATCH (m:Medication {name: 'Metformina'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) MERGE (m)-[r:TREATS]->(c) ON CREATE SET r.created_at = timestamp();",
    "MATCH (f:Food {name: 'Brócolis'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) MERGE (f)-[r:IS_RECOMMENDED_FOR]->(c) ON CREATE SET r.created_at = timestamp();",
    "MATCH (f:Food {name: 'Arroz Branco'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) MERGE (f)-[r:IS_NOT_RECOMMENDED_FOR]->(c) ON CREATE SET r.created_at = timestamp();",
]

class Neo4jPopulater:
    def __init__(self, uri: str, user: str, password: str | None):
        if not all([uri, user, password]):
            raise ValueError("Credenciais Neo4j incompletas para Neo4jPopulater.")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            logger.info(f"Neo4jPopulater conectado com sucesso a {uri}.")
        except neo4j_exceptions.ServiceUnavailable as e:
            logger.error(f"Serviço Neo4j indisponível em {uri}: {e}")
            raise
        except neo4j_exceptions.AuthError as e:
            logger.error(f"Erro de autenticação ao conectar ao Neo4j em {uri}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao inicializar Neo4jPopulater com {uri}: {e}", exc_info=True)
            raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Conexão do Neo4jPopulater fechada.")

    def populate_kg(self):
        logger.info("Populando o Grafo de Conhecimento Médico com queries idempotentes...")
        try:
            with self.driver.session() as session:
                for i, query in enumerate(CYPHER_QUERIES):
                    logger.debug(f"Executando query {i+1}/{len(CYPHER_QUERIES)}: {query[:100]}...")
                    session.run(query)
                logger.info(f"Grafo de Conhecimento populado/atualizado com sucesso! {len(CYPHER_QUERIES)} queries executadas.")
        except Exception as e:
            logger.error(f"Erro inesperado ao popular o KG: {e}", exc_info=True)


def full_reset():
    logger.info("Executando reset completo do ambiente...")
    reset_neo4j()
    reset_vectorstore()
    logger.info("Reset completo do ambiente finalizado.")

def populate_medical_kg():
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_pass = os.getenv("NEO4J_PASSWORD")
    if not all([neo4j_uri, neo4j_user, neo4j_pass]):
        logger.error("Credenciais do Neo4j não encontradas. Não é possível popular o KG.")
        return
    populater_instance = None
    try:
        populater_instance = Neo4jPopulater(neo4j_uri, neo4j_user, neo4j_pass)
        populater_instance.populate_kg()
    except Exception as e:
        logger.error(f"Erro geral ao popular o KG médico: {e}", exc_info=True)
    finally:
        if populater_instance:
            populater_instance.close()

# MODIFICADO: Nova função para ingerir documentos locais
def ingest_local_documents():
    """
    Escaneia o diretório 'knowledge_sources/pdfs' e ingere cada documento PDF encontrado.
    """
    logger.info("--- Iniciando ingestão de documentos locais ---")
    local_pdf_path = os.path.join("knowledge_sources", "pdfs")
    
    if not os.path.isdir(local_pdf_path):
        logger.warning(f"Diretório de PDFs locais '{local_pdf_path}' não encontrado. Nenhum documento será ingerido.")
        return
        
    if not kb_manager:
        logger.error("KnowledgeBaseManager não está disponível. Não é possível ingerir documentos locais.")
        return

    pdf_files = [f for f in os.listdir(local_pdf_path) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logger.info(f"Nenhum arquivo PDF encontrado em '{local_pdf_path}'.")
        return

    logger.info(f"Encontrados {len(pdf_files)} arquivos PDF para ingestão.")
    for pdf_file in pdf_files:
        full_path = os.path.join(local_pdf_path, pdf_file)
        logger.info(f"Processando arquivo: {full_path}")
        try:
            # A função ingest_new_document já verifica se o documento existe
            result = kb_manager.ingest_new_document(file_path=full_path)
            logger.info(f"Resultado da ingestão para '{pdf_file}': {result}")
        except Exception as e:
            logger.error(f"Falha ao ingerir o documento local '{pdf_file}': {e}", exc_info=True)

    logger.info("--- Ingestão de documentos locais concluída ---")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s')

    parser = argparse.ArgumentParser(description="Gerencia a base de dados da aplicação PROVIDA.")
    parser.add_argument("--reset", action="store_true", help="Limpa completamente o ambiente (Neo4j e VectorDB).")
    parser.add_argument("--populate", action="store_true", help="Popula o Grafo de Conhecimento no Neo4j com dados básicos.")
    # MODIFICADO: Novo argumento para ingestão local
    parser.add_argument("--ingest-local", action="store_true", help="Ingere documentos PDF do diretório 'knowledge_sources/pdfs'.")
    
    args = parser.parse_args()

    if not any([args.reset, args.populate, args.ingest_local]):
        parser.print_help()
        logger.info("\nPor favor, especifique uma ação: --reset, --populate, e/ou --ingest-local.")
    
    if args.reset:
        try:
            confirm = input("Você tem CERTEZA ABSOLUTA que deseja deletar TODOS os dados? [digite 'sim' para confirmar]: ")
            if confirm.lower() == 'sim':
                logger.info("Confirmação recebida para reset.")
                full_reset()
            else:
                logger.info("Operação de reset cancelada.")
        except KeyboardInterrupt:
            logger.info("\nOperação de reset interrompida.")

    if args.populate:
        populate_medical_kg()
        
    # MODIFICADO: Chama a nova função se o argumento for fornecido
    if args.ingest_local:
        ingest_local_documents()

    logger.info("\nOperações do script concluídas.")
