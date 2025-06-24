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
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

VECTORSTORE_PATH = "./faiss_index"
"""Caminho para o diretório do índice FAISS."""

SOURCES_DIR = "./knowledge_sources"
"""Diretório raiz para as fontes de conhecimento."""

CONTENT_HASH_LOG = os.path.join(SOURCES_DIR, "content_hashes.log")
"""Caminho para o arquivo de log que armazena hashes de conteúdo de documentos processados."""

UPLOADS_DIR = os.path.join(SOURCES_DIR, "uploads")
"""Diretório para arquivos de documentos enviados via API antes do processamento."""

DOWNLOADS_DIR = os.path.join(SOURCES_DIR, "downloads")
"""Diretório para arquivos de documentos baixados pelo agente de pesquisa."""

def reset_neo4j():
    """
    Limpa completamente o banco de dados Neo4j.

    Conecta-se ao Neo4j usando as credenciais do ambiente e executa uma query
    Cypher (`MATCH (n) DETACH DELETE n`) para remover todos os nós e seus
    relacionamentos.
    """
    uri, user, password = os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            print("Limpando banco de dados Neo4j...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Neo4j limpo com sucesso.")
        driver.close()
    except Exception as e:
        print(f"Erro ao limpar o Neo4j: {e}")

def reset_vectorstore():
    """
    Remove o índice vetorial FAISS, logs relacionados e diretórios de arquivos temporários.

    Deleta recursivamente os seguintes diretórios (se existirem):
    - `VECTORSTORE_PATH` (índice FAISS)
    - `UPLOADS_DIR` (arquivos de upload)
    - `DOWNLOADS_DIR` (arquivos baixados)
    E remove o arquivo `CONTENT_HASH_LOG`.
    """
    print("Limpando banco de dados vetorial, logs e arquivos temporários...")
    
    for path in [VECTORSTORE_PATH, UPLOADS_DIR, DOWNLOADS_DIR]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"- Diretório '{path}' removido.")
            except OSError as e:
                print(f"Erro ao remover o diretório {path}: {e}")

    if os.path.exists(CONTENT_HASH_LOG):
        try:
            os.remove(CONTENT_HASH_LOG)
            print(f"- Arquivo de log '{CONTENT_HASH_LOG}' removido.")
        except OSError as e:
            print(f"Erro ao remover o arquivo {CONTENT_HASH_LOG}: {e}")
            
    print("Limpeza concluída.")

if __name__ == "__main__":
    """
    Ponto de entrada principal para o script quando executado.

    Configura o parser de argumentos de linha de comando para a ação `--yes-i-am-sure`.
    Se a flag for fornecida, executa as funções de reset. Caso contrário,
    informa o usuário sobre a necessidade da flag de confirmação.
    """
    parser = argparse.ArgumentParser(description="Reseta o ambiente de dados da aplicação PROVIDA.")
    parser.add_argument("--yes-i-am-sure", action="store_true", help="Confirmação para executar o reset.")
    args = parser.parse_args()

    if args.yes_i_am_sure:
        print("--- INICIANDO RESET COMPLETO DO AMBIENTE ---")
        reset_neo4j()
        reset_vectorstore()
        print("--- RESET COMPLETO CONCLUÍDO ---")
    else:
        print("Operação cancelada. Use a flag --yes-i-am-sure para confirmar.")
