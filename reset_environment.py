import os
import shutil
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

VECTORSTORE_PATH = "./faiss_index"
SOURCES_DIR = "./knowledge_sources"
CONTENT_HASH_LOG = os.path.join(SOURCES_DIR, "content_hashes.log")
UPLOADS_DIR = os.path.join(SOURCES_DIR, "uploads")
DOWNLOADS_DIR = os.path.join(SOURCES_DIR, "downloads")

def reset_neo4j():
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
