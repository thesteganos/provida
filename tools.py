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
import logging
from typing import List, Dict, Any, Union
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def patient_kg_query_tool(patient_id: str) -> Union[List[Dict[str, Any]], str]:
    """
    Busca os dados clínicos estruturados de um paciente específico no Grafo de Conhecimento (Neo4j).
    """
    from kb_manager import kb_manager

    if not patient_id or not isinstance(patient_id, str):
        logger.warning("patient_kg_query_tool: patient_id inválido ou ausente.")
        return "Erro: ID do paciente inválido ou não fornecido para a busca no KG."

    cypher_query = "MATCH (p:Patient {id: $patient_id_param}) RETURN p"
    params = {"patient_id_param": patient_id}

    logger.debug(f"Executando query parametrizada no KG para patient_id='{patient_id}'")

    if kb_manager and kb_manager.graph:
        try:
            result: List[Dict[str, Any]] = kb_manager.graph.query(cypher_query, params=params)
            if not result:
                logger.info(f"Nenhum paciente encontrado no KG com ID: {patient_id}")
                return [] 
            return result
        except Exception as e:
            logger.error(f"Erro ao executar query no KG para patient_id='{patient_id}': {e}", exc_info=True)
            return f"Erro ao consultar a base de dados do paciente: {e}"
    else:
        logger.error(f"patient_kg_query_tool: Neo4j graph ou kb_manager não estão disponíveis. Patient ID: {patient_id}")
        return "Erro: A conexão com a base de dados de pacientes (Neo4j) não está disponível."

@tool
def rag_evidence_search_tool(topic: str) -> str:
    """
    Busca por evidências em documentos médicos e diretrizes (via RAG) para um determinado tópico.
    """
    from kb_manager import kb_manager

    if not topic or not isinstance(topic, str):
        logger.warning("rag_evidence_search_tool: 'topic' inválido ou ausente.")
        return "Erro: Tópico de busca inválido ou não fornecido para a pesquisa de evidências."

    logger.debug(f"Executando busca RAG para o tópico: '{topic[:100]}...'")

    if not kb_manager:
        logger.error("rag_evidence_search_tool: kb_manager não está disponível.")
        return "Erro: O Gerenciador da Base de Conhecimento não está disponível."
        
    try:
        return kb_manager.rag_query(topic)
    except Exception as e:
        logger.error(f"Erro inesperado ao executar rag_evidence_search_tool para o tópico '{topic}': {e}", exc_info=True)
        return f"Erro ao realizar a busca por evidências: {e}"
