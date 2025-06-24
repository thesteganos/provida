# tools.py
from langchain_core.tools import tool
from kb_manager import kb_manager

@tool
def patient_kg_query_tool(patient_id: str) -> list:
    """
    Busca os dados clínicos estruturados de um paciente específico no Grafo de Conhecimento.
    Forneça apenas o ID do paciente. A query Cypher para buscar os dados do paciente é fixa.
    Use esta ferramenta para obter informações como nome, idade, IMC, HbA1c e notas clínicas.
    """
    # A query Cypher é fixa para buscar todos os dados do nó do paciente.
    cypher_query = f"MATCH (p:Patient {{id: '{patient_id}'}}) RETURN p"
    print(f"Executando query no KG para patient_id='{patient_id}': {cypher_query}")
    return kb_manager.graph.query(cypher_query)

@tool
def rag_evidence_search_tool(topic: str) -> str:
    """
    Busca por evidências em documentos médicos e diretrizes (via RAG)
    para um determinado tópico ou pergunta.
    """
    return kb_manager.rag_query(topic)
