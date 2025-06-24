import os
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv
from reset_environment import reset_neo4j, reset_vectorstore

load_dotenv()

CYPHER_QUERIES = [
    "CREATE (:Guideline {name: 'PCDT Sobrepeso e Obesidade', source: 'MS-2024'});",
    "CREATE (:Condition {name: 'Obesidade Grau I', min_imc: 30.0, max_imc: 34.9});",
    "CREATE (:Condition {name: 'Diabetes Mellitus Tipo 2'});",
    "CREATE (:Medication {name: 'Metformina'});",
    "CREATE (:Medication {name: 'Semaglutida'});",
    "CREATE (:Food {name: 'Brócolis', glycemic_index: 15, type: 'vegetal'});",
    "CREATE (:Food {name: 'Arroz Branco', glycemic_index: 73, type: 'carboidrato'});",
    "MATCH (g:Guideline {name: 'PCDT Sobrepeso e Obesidade'}), (c:Condition {name: 'Obesidade Grau I'}) CREATE (g)-[:RECOMMENDS_TREATMENT_FOR]->(c);",
    "MATCH (m:Medication {name: 'Metformina'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) CREATE (m)-[:TREATS]->(c);",
    "MATCH (f:Food {name: 'Brócolis'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) CREATE (f)-[:IS_RECOMMENDED_FOR]->(c);",
    "MATCH (f:Food {name: 'Arroz Branco'}), (c:Condition {name: 'Diabetes Mellitus Tipo 2'}) CREATE (f)-[:IS_NOT_RECOMMENDED_FOR]->(c);",
]

class Neo4jPopulater:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def populate_kg(self):
        print("Populando o Grafo de Conhecimento Médico...")
        with self.driver.session() as session:
            for i, query in enumerate(CYPHER_QUERIES):
                session.run(query)
                print(f"  - Query {i+1}/{len(CYPHER_QUERIES)} executada.")
        print("Grafo de Conhecimento populado com sucesso!")

def full_reset():
    print("Executando reset completo do ambiente...")
    reset_neo4j()
    reset_vectorstore()
    print("Reset completo finalizado.")

def populate_medical_kg():
    try:
        populater = Neo4jPopulater(
            os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")
        )
        populater.populate_kg()
    except Exception as e:
        print(f"Erro ao popular o KG médico: {e}")
    finally:
        if 'populater' in locals() and populater.driver:
            populater.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerencia a base de dados da aplicação PROVIDA.")
    parser.add_argument("--reset", action="store_true", help="Limpa completamente TODO o ambiente (Neo4j e VectorDB). ATENÇÃO: IRREVERSÍVEL.")
    parser.add_argument("--populate", action="store_true", help="Popula o Grafo de Conhecimento Médico no Neo4j com dados iniciais.")
    args = parser.parse_args()

    if not args.reset and not args.populate:
        parser.print_help()
        print("\nPor favor, especifique uma ação: --reset e/ou --populate.")
    
    if args.reset:
        confirm = input("Você tem CERTEZA que deseja deletar TODOS os dados (Neo4j e VectorDB)? [s/N]: ")
        if confirm.lower() == 's':
            full_reset()
        else:
            print("Operação de reset cancelada.")

    if args.populate:
        populate_medical_kg()

    print("\nOperação concluída.")
