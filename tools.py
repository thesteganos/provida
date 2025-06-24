# tools.py
from langchain_core.tools import tool
from kb_manager import kb_manager

@tool
def patient_kg_query_tool(patient_id: str, cypher_query: str) -> list:
    """
    Executa uma query Cypher no Grafo de Conhecimento do Paciente para obter dados clínicos estruturados.
    Use para verificar comorbidades, dados demográficos, etc.
    """
    # Em uma implementação real, a query poderia ser gerada por um LLM.
    # Por simplicidade, usamos uma query fixa para buscar os dados do paciente.
    query = f"MATCH (p:Patient {{id: '{patient_id}'}}) RETURN p"
    return kb_manager.graph.query(query)

@tool
def rag_evidence_search_tool(topic: str) -> str:
    """
    Busca por evidências em documentos médicos e diretrizes (via RAG)
    para um determinado tópico ou pergunta.
    """
    return kb_manager.rag_query(topic)
