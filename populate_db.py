"""
Este script é uma ferramenta de linha de comando para gerenciar a base de dados da aplicação PROVIDA.

Ele oferece funcionalidades para:
1. Resetar o ambiente:
    - Limpar completamente o banco de dados Neo4j.
    - Remover o índice vetorial FAISS e arquivos de log associados.
2. Popular o Grafo de Conhecimento Médico:
    - Inserir dados iniciais (nós e relacionamentos) no Neo4j, como diretrizes,
      condições médicas, medicamentos e alimentos.

Utiliza `argparse` para processar argumentos de linha de comando e interage
diretamente com o Neo4j e o sistema de arquivos para realizar as operações.
As queries Cypher para popular o KG estão definidas na constante `CYPHER_QUERIES`.
Depende do `reset_environment.py` para as funções de limpeza.
"""
import os
import argparse
import logging # Adicionado logging
from neo4j import GraphDatabase, exceptions as neo4j_exceptions # Importa exceções específicas
from dotenv import load_dotenv
from reset_environment import reset_neo4j, reset_vectorstore # Funções de reset atualizadas

load_dotenv()
logger = logging.getLogger(__name__)

# Queries Cypher para popular o KG.
# Tornadas idempotentes usando MERGE para nós e MERGE para relacionamentos
# para evitar duplicação se o script for executado várias vezes sem reset.
CYPHER_QUERIES = [
    # Nós
    "MERGE (g:Guideline {name: 'PCDT Sobrepeso e Obesidade'}) ON CREATE SET g.source = 'MS-2024', g.created_at = timestamp() ON MATCH SET g.updated_at = timestamp();",
    "MERGE (c1:Condition {name: 'Obesidade Grau I'}) ON CREATE SET c1.min_imc = 30.0, c1.max_imc = 34.9, c1.created_at = timestamp() ON MATCH SET c1.updated_at = timestamp();",
    "MERGE (c2:Condition {name: 'Diabetes Mellitus Tipo 2'}) ON CREATE SET c2.created_at = timestamp() ON MATCH SET c2.updated_at = timestamp();",
    "MERGE (m1:Medication {name: 'Metformina'}) ON CREATE SET m1.created_at = timestamp() ON MATCH SET m1.updated_at = timestamp();",
    "MERGE (m2:Medication {name: 'Semaglutida'}) ON CREATE SET m2.created_at = timestamp() ON MATCH SET m2.updated_at = timestamp();",
    "MERGE (f1:Food {name: 'Brócolis'}) ON CREATE SET f1.glycemic_index = 15, f1.type = 'vegetal', f1.created_at = timestamp() ON MATCH SET f1.updated_at = timestamp();",
    "MERGE (f2:Food {name: 'Arroz Branco'}) ON CREATE SET f2.glycemic_index = 73, f2.type = 'carboidrato', f2.created_at = timestamp() ON MATCH SET f2.updated_at = timestamp();",

    # Relacionamentos (usando MERGE para criar apenas se não existir)
    "MATCH (g:Guideline {name: 'PCDT Sobrepeso e Obesidade'}), (c:Condition {name: 'Obesidade Grau I'}) MERGE (g)-[r:RECOMMENDS_TREATMENT_FOR]->(c) ON CREATE SET r.created_at = timestamp();",
    "MATCH (m:Medication {name: 'Metformina'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) MERGE (m)-[r:TREATS]->(c) ON CREATE SET r.created_at = timestamp();",
    "MATCH (f:Food {name: 'Brócolis'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) MERGE (f)-[r:IS_RECOMMENDED_FOR]->(c) ON CREATE SET r.created_at = timestamp();",
    "MATCH (f:Food {name: 'Arroz Branco'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) MERGE (f)-[r:IS_NOT_RECOMMENDED_FOR]->(c) ON CREATE SET r.created_at = timestamp();",
]

class Neo4jPopulater:
    """
    Classe responsável por popular o banco de dados Neo4j com dados iniciais.
    """
    def __init__(self, uri: str, user: str, password: str | None): # Password pode ser None
        """
        Inicializa o Neo4jPopulater e estabelece a conexão com o banco.
        """
        if not all([uri, user, password]): # Verifica se as credenciais são válidas
            logger.error("Credenciais do Neo4j (URI, USERNAME, PASSWORD) não estão completamente definidas. Não é possível inicializar o Neo4jPopulater.")
            # Levantar um erro aqui pode ser mais apropriado do que continuar com um driver inválido.
            raise ValueError("Credenciais Neo4j incompletas para Neo4jPopulater.")

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity() # Verifica a conexão na inicialização
            logger.info(f"Neo4jPopulater conectado com sucesso a {uri}.")
        except neo4j_exceptions.ServiceUnavailable as e:
            logger.error(f"Serviço Neo4j indisponível em {uri} para Neo4jPopulater: {e}")
            raise
        except neo4j_exceptions.AuthError as e:
            logger.error(f"Erro de autenticação ao conectar ao Neo4j em {uri} para Neo4jPopulater: {e}")
            raise
        except Exception as e: # Outras exceções
            logger.error(f"Erro inesperado ao inicializar Neo4jPopulater com {uri}: {e}", exc_info=True)
            raise


    def close(self):
        """Fecha a conexão do driver do Neo4j."""
        if self.driver:
            self.driver.close()
            logger.info("Conexão do Neo4jPopulater fechada.")

    def populate_kg(self):
        """
        Executa as queries Cypher predefinidas para popular o grafo de conhecimento.
        As queries são projetadas para serem idempotentes usando MERGE.
        """
        logger.info("Populando o Grafo de Conhecimento Médico com queries idempotentes...")
        try:
            with self.driver.session() as session:
                for i, query in enumerate(CYPHER_QUERIES):
                    logger.debug(f"Executando query de população {i+1}/{len(CYPHER_QUERIES)}: {query[:100]}...")
                    session.run(query)
                logger.info(f"Grafo de Conhecimento populado/atualizado com sucesso! {len(CYPHER_QUERIES)} queries executadas.")
        except neo4j_exceptions.Neo4jError as e: # Erros específicos do Neo4j durante a query
            logger.error(f"Erro Neo4j ao popular o KG: {e}", exc_info=True)
            # Pode-se decidir se quer relançar o erro ou não.
        except Exception as e: # Outros erros
            logger.error(f"Erro inesperado ao popular o KG: {e}", exc_info=True)


def full_reset():
    """
    Executa um reset completo do ambiente de dados.
    """
    logger.info("Executando reset completo do ambiente...")
    reset_neo4j()       # Função importada de reset_environment.py (já loga internamente)
    reset_vectorstore() # Função importada de reset_environment.py (já loga internamente)
    logger.info("Reset completo do ambiente finalizado.")

def populate_medical_kg():
    """
    Cria uma instância de `Neo4jPopulater` e chama seu método `populate_kg`.
    """
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_pass = os.getenv("NEO4J_PASSWORD")

    if not all([neo4j_uri, neo4j_user, neo4j_pass]):
        logger.error("Credenciais do Neo4j (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) não encontradas nas variáveis de ambiente. Não é possível popular o KG.")
        return

    populater_instance = None # Para garantir que close() seja chamado corretamente no finally
    try:
        populater_instance = Neo4jPopulater(neo4j_uri, neo4j_user, neo4j_pass)
        populater_instance.populate_kg()
    except ValueError: # Erro de inicialização do Neo4jPopulater devido a credenciais
        # A mensagem de erro já foi logada pelo construtor do Neo4jPopulater
        pass
    except Exception as e: # Outros erros durante a população
        logger.error(f"Erro geral ao popular o KG médico: {e}", exc_info=True)
    finally:
        if populater_instance:
            populater_instance.close()

if __name__ == "__main__":
    """
    Ponto de entrada principal para o script quando executado.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Gerencia a base de dados da aplicação PROVIDA (reset e/ou população inicial)."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Limpa completamente TODO o ambiente (Neo4j e VectorDB). ATENÇÃO: IRREVERSÍVEL."
    )
    parser.add_argument(
        "--populate",
        action="store_true",
        help="Popula o Grafo de Conhecimento Médico no Neo4j com dados iniciais (usa MERGE, então é idempotente)."
    )
    args = parser.parse_args()

    if not args.reset and not args.populate:
        parser.print_help()
        logger.info("\nPor favor, especifique uma ação: --reset e/ou --populate.")
    
    if args.reset:
        # A confirmação do usuário é crucial para operações destrutivas.
        try:
            confirm = input("Você tem CERTEZA ABSOLUTA que deseja deletar TODOS os dados (Neo4j e VectorDB)? Esta ação é IRREVERSÍVEL. [digite 'sim' para confirmar]: ")
            if confirm.lower() == 'sim':
                logger.info("Confirmação recebida para reset.")
                full_reset()
            else:
                logger.info("Operação de reset cancelada pelo usuário.")
        except KeyboardInterrupt:
            logger.info("\nOperação de reset interrompida pelo usuário.")

    if args.populate:
        populate_medical_kg()

    logger.info("\nOperações do script de população/reset concluídas.")
