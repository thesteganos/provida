# tools.py
"""
Este módulo define as ferramentas (tools) LangChain que os agentes podem utilizar.

As ferramentas são funções decoradas com `@tool` que permitem aos agentes interagir
com sistemas externos ou executar operações específicas. Neste caso, as ferramentas
interagem com o `KnowledgeBaseManager` para acessar o grafo de conhecimento Neo4j
e a base de dados vetorial RAG.

Ferramentas definidas:
- `patient_kg_query_tool`: Busca dados clínicos de um paciente no Neo4j.
- `rag_evidence_search_tool`: Busca evidências em documentos médicos via RAG.
"""
from langchain_core.tools import tool
from kb_manager import kb_manager

@tool
def patient_kg_query_tool(patient_id: str) -> list:
    """
    Busca os dados clínicos estruturados de um paciente específico no Grafo de Conhecimento (Neo4j).

    Esta ferramenta é projetada para ser usada por agentes que precisam acessar
    informações detalhadas de um paciente. A query Cypher é fixa para buscar todas as
    propriedades do nó :Patient correspondente ao `patient_id` fornecido.

    Args:
        patient_id (str): O identificador único do paciente cujos dados devem ser buscados.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um nó encontrado
              (espera-se geralmente um único nó de paciente). As chaves do dicionário
              são as propriedades do nó no Neo4j. Retorna uma lista vazia se nenhum
              paciente for encontrado ou se a conexão com o Neo4j falhar.
              Exemplo de retorno: `[{'p': {'id': 'xyz', 'name': 'Fulano', 'age': 30, ...}}]`

    Raises:
        Pode levantar exceções relacionadas à conexão com o Neo4j se o `kb_manager.graph`
        não estiver disponível ou se a query falhar.
    """
    # A query Cypher é fixa para buscar todos os dados do nó do paciente.
    cypher_query = f"MATCH (p:Patient {{id: '{patient_id}'}}) RETURN p"
    print(f"Executando query no KG para patient_id='{patient_id}': {cypher_query}")
    if kb_manager.graph:
        return kb_manager.graph.query(cypher_query)
    logging.error(f"patient_kg_query_tool: Neo4j graph não está disponível. Patient ID: {patient_id}")
    return []

@tool
def rag_evidence_search_tool(topic: str) -> str:
    """
    Busca por evidências em documentos médicos e diretrizes (via RAG) para um determinado tópico.

    Utiliza o `kb_manager.rag_query()` para realizar a busca na base de conhecimento
    vetorial (FAISS). É útil para agentes que precisam fundamentar suas respostas
    ou planos em evidências textuais.

    Args:
        topic (str): O tópico, pergunta ou termo de busca para encontrar evidências relevantes.

    Returns:
        str: Uma string contendo os trechos de documentos encontrados, formatados
             com a fonte e o conteúdo. Retorna uma mensagem indicando que nenhuma
             informação foi encontrada se a busca não retornar resultados.
    """
    return kb_manager.rag_query(topic)

# Adicionado import de logging que faltava para o error handling em patient_kg_query_tool
import logging
