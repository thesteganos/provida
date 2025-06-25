# agents.py
"""
Este módulo define os agentes LangChain do sistema PROVIDA.

Os agentes são responsáveis por orquestrar a lógica de tomada de decisão,
utilizando LLMs, ferramentas (tools) e prompts para realizar tarefas complexas.

Agentes definidos:
- `clinical_agent_executor`: Um agente executor projetado para analisar dados de
  pacientes e fornecer recomendações clínicas com base em evidências. Ele é
  construído usando a função `create_openai_tools_agent` da LangChain, que
  permite que o LLM escolha dinamicamente as ferramentas a serem usadas.
"""
import logging
from typing import List

# MODIFICADO: Importando de pydantic.v1 para corrigir o aviso de deprecação
from pydantic.v1 import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage

# Módulos locais
from prompts import CLINICAL_AGENT_PROMPT
from tools import patient_kg_query_tool, rag_evidence_search_tool
from config_loader import config

logger = logging.getLogger(__name__)

# Define o estado do agente, que é passado entre os nós do grafo LangGraph
class AgentState(BaseModel):
    """
    Representa o estado do agente durante a execução.
    Inclui o input inicial e o histórico de mensagens da conversa.
    """
    input: str
    chat_history: List[BaseMessage] = Field(
        ...,
        extra={"is_chat_history": True}
    )

# Lista de ferramentas que o agente clínico pode usar
clinical_agent_tools = [patient_kg_query_tool, rag_evidence_search_tool]

try:
    # Carrega o LLM configurado para o agente clínico
    llm = config.get_llm('clinical_agent')
    # Cria o agente usando o LLM, as ferramentas e o prompt
    clinical_agent = create_openai_tools_agent(
        llm=llm,
        tools=clinical_agent_tools,
        prompt=CLINICAL_AGENT_PROMPT
    )
    # Cria o executor do agente, que efetivamente roda os ciclos de pensamento/ação
    clinical_agent_executor = AgentExecutor(
        agent=clinical_agent,
        tools=clinical_agent_tools,
        verbose=True # Ativa o logging detalhado para depuração
    )
    logger.info("Agente clínico e executor criados com sucesso.")
except ValueError as e:
    logger.critical(f"Falha ao criar o agente clínico: {e}", exc_info=True)
    # Define o executor como None para que a falha seja clara em outras partes do sistema
    clinical_agent_executor = None
except Exception as e:
    logger.critical(f"Um erro inesperado ocorreu ao criar o agente clínico: {e}", exc_info=True)
    clinical_agent_executor = None
