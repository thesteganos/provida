"""
Este script fornece funcionalidades para resetar o ambiente de dados da aplicação PROVIDA.

Ele pode ser executado como um script de linha de comando para:
1. Limpar todos os dados do banco de dados Neo4j.
2. Remover o índice vetorial FAISS, o log de hashes de conteúdo e
   os diretórios de uploads e downloads de documentos.

Define constantes para os caminhos de diretórios e arquivos relevantes.
As funções `reset_neo4j` e `reset_vectorstore` encapsulam a lógica de limpeza
para cada componente da base de dados.

É importante notar que esta é uma operação destrutiva e deve ser usada com cautela.
O script requer uma flag de confirmação (`--yes-i-am-sure`) para ser executado.
"""
import os
import shutil
import argparse
import logging # Adicionado logging
from neo4j import GraphDatabase, exceptions as neo4j_exceptions # Importa exceções específicas
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

VECTORSTORE_PATH = "./faiss_index"
"""Caminho para o diretório do índice FAISS."""

SOURCES_DIR = "./knowledge_sources"
"""Diretório raiz para as fontes de conhecimento."""

# Caminho atualizado para o log de hashes, conforme usado em kb_manager.py
CONTENT_HASH_LOG = os.path.join(SOURCES_DIR, "processed_document_content_hashes.log")
"""Caminho para o arquivo de log que armazena hashes de conteúdo de documentos processados."""

# Diretório de uploads temporários usado por main.py
UPLOADS_TEMP_DIR = os.path.join(SOURCES_DIR, "uploads_temp")
"""Diretório para arquivos de documentos enviados via API e armazenados temporariamente."""

# Diretório de downloads do research_worker.py
DOWNLOADS_RESEARCH_DIR = os.path.join(SOURCES_DIR, "downloads_research_worker")
"""Diretório para arquivos de documentos baixados pelo agente de pesquisa."""


def reset_neo4j():
    """
    Limpa completamente o banco de dados Neo4j.

    Conecta-se ao Neo4j usando as credenciais do ambiente e executa uma query
    Cypher (`MATCH (n) DETACH DELETE n`) para remover todos os nós e seus
    relacionamentos.
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        logger.error("Credenciais do Neo4j (URI, USERNAME, PASSWORD) não estão completamente definidas no ambiente. Reset do Neo4j pulado.")
        return

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            logger.info(f"Limpando banco de dados Neo4j em {uri}...")
            # Verifica se há nós antes de tentar deletar para evitar erros em DBs vazios e para log
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            node_count = result.single()["node_count"]

            if node_count > 0:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info(f"Neo4j limpo com sucesso. {node_count} nós foram removidos.")
            else:
                logger.info("Neo4j já estava vazio. Nenhuma ação de remoção de nós necessária.")
        driver.close()
    except neo4j_exceptions.ServiceUnavailable as e:
        logger.error(f"Não foi possível conectar ao Neo4j em {uri} para reset: {e}")
    except neo4j_exceptions.AuthError as e:
        logger.error(f"Erro de autenticação ao conectar ao Neo4j em {uri} para reset: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao limpar o Neo4j: {e}", exc_info=True)

def reset_vectorstore():
    """
    Remove o índice vetorial FAISS, logs relacionados e diretórios de arquivos temporários.

    Deleta recursivamente os seguintes diretórios (se existirem):
    - `VECTORSTORE_PATH` (índice FAISS)
    - `UPLOADS_TEMP_DIR` (arquivos de upload temporários da API)
    - `DOWNLOADS_RESEARCH_DIR` (arquivos baixados pelo research_worker)
    E remove o arquivo `CONTENT_HASH_LOG`.
    """
    logger.info("Limpando banco de dados vetorial, logs e arquivos temporários...")
    
    paths_to_remove = [
        VECTORSTORE_PATH,
        UPLOADS_TEMP_DIR,
        DOWNLOADS_RESEARCH_DIR
    ]

    for path_dir in paths_to_remove:
        if os.path.exists(path_dir) and os.path.isdir(path_dir): # Verifica se é diretório
            try:
                shutil.rmtree(path_dir)
                logger.info(f"- Diretório '{path_dir}' removido com sucesso.")
            except OSError as e:
                logger.error(f"Erro ao remover o diretório '{path_dir}': {e}")
        elif os.path.exists(path_dir): # Se existir mas não for diretório (improvável para estes)
             logger.warning(f"Caminho '{path_dir}' existe mas não é um diretório. Não foi removido por rmtree.")


    if os.path.exists(CONTENT_HASH_LOG) and os.path.isfile(CONTENT_HASH_LOG): # Verifica se é arquivo
        try:
            os.remove(CONTENT_HASH_LOG)
            logger.info(f"- Arquivo de log '{CONTENT_HASH_LOG}' removido com sucesso.")
        except OSError as e:
            logger.error(f"Erro ao remover o arquivo de log '{CONTENT_HASH_LOG}': {e}")
    elif os.path.exists(CONTENT_HASH_LOG):
        logger.warning(f"Caminho '{CONTENT_HASH_LOG}' existe mas não é um arquivo. Não foi removido por os.remove.")
            
    logger.info("Limpeza de arquivos e diretórios do VectorStore concluída.")

if __name__ == "__main__":
    """
    Ponto de entrada principal para o script quando executado.
    """
    # Configuração básica de logging para o script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Reseta o ambiente de dados da aplicação PROVIDA (Neo4j, FAISS, logs e arquivos temporários). ATENÇÃO: Operação destrutiva."
    )
    parser.add_argument(
        "--yes-i-am-sure",
        action="store_true",
        help="Confirmação OBRIGATÓRIA para executar o reset. Sem esta flag, nada será feito."
    )
    args = parser.parse_args()

    if args.yes_i_am_sure:
        logger.info("--- INICIANDO RESET COMPLETO DO AMBIENTE ---")
        reset_neo4j()
        reset_vectorstore()
        logger.info("--- RESET COMPLETO CONCLUÍDO ---")
    else:
        logger.warning("Operação de reset cancelada. É necessário usar a flag --yes-i-am-sure para confirmar a execução.")
        parser.print_help()
