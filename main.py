# main.py
"""
Ponto de entrada principal da API do PROVIDA, utilizando FastAPI.

Esta aplicação expõe endpoints para interagir com os agentes inteligentes
do sistema. O principal endpoint é `/invoke`, que permite aos clientes
enviarem uma consulta para o agente clínico e receberem uma resposta
fundamentada em evidências e dados do paciente.

Endpoints:
- `/`: Endpoint raiz para verificação de status.
- `/invoke`: Endpoint principal para interagir com o agente clínico.

A aplicação gerencia um histórico de sessão simples para manter o contexto
em conversas contínuas com o mesmo cliente (identificado por `session_id`).
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any

# MODIFICADO: Importando de pydantic.v1 para corrigir o aviso de deprecação
from pydantic.v1 import BaseModel

# Módulos locais
from agents import clinical_agent_executor
from config_loader import config

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="ProVida API",
    description="API para interação com os Agentes Inteligentes ProVida.",
    version="1.o.o"
)

# Configuração do CORS para permitir requisições do frontend
origins = config.get_allowed_origins()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS configurado para as origens: {origins}")

# Dicionário para armazenar o histórico de chat por sessão
# Em um ambiente de produção, isso seria substituído por um banco de dados como Redis.
session_histories: Dict[str, List[Dict[str, Any]]] = {}

# Modelo Pydantic para a requisição do endpoint /invoke
class PatientQuery(BaseModel):
    """

    Define a estrutura da requisição para o endpoint /invoke.
    """
    patient_id: str
    question: str
    session_id: str

@app.get("/")
def read_root():
    """
    Endpoint raiz para verificar se a API está no ar.
    """
    return {"status": "ProVida API is running"}

@app.post("/invoke")
async def invoke_agent(query: PatientQuery):
    """
    Endpoint principal para invocar o agente clínico.

    Recebe uma consulta contendo o ID do paciente e uma pergunta.
    Gerencia o histórico da conversa e chama o executor do agente.
    """
    if not clinical_agent_executor:
        logger.error("Tentativa de chamada ao endpoint /invoke, mas o agente clínico não foi inicializado.")
        raise HTTPException(status_code=500, detail="Internal Server Error: Clinical agent not available.")

    logger.info(f"Recebida requisição para session_id: {query.session_id}, patient_id: {query.patient_id}")

    # Recupera ou inicializa o histórico da sessão
    if query.session_id not in session_histories:
        session_histories[query.session_id] = []
    
    chat_history_list = session_histories[query.session_id]
    
    # Converte o histórico de dicionários para objetos de mensagem LangChain
    chat_history_messages = []
    for item in chat_history_list:
        if item.get("type") == "human":
            chat_history_messages.append(HumanMessage(content=item["content"]))
        elif item.get("type") == "ai":
            chat_history_messages.append(AIMessage(content=item["content"]))

    # Monta o input para o agente
    agent_input = {
        "patient_id": query.patient_id,
        "input": query.question,
        "chat_history": chat_history_messages
    }

    try:
        # Invoca o agente com o input
        logger.debug(f"Invocando agente para session_id: {query.session_id} com a pergunta: '{query.question}'")
        response = await clinical_agent_executor.ainvoke(agent_input)
        logger.debug(f"Agente respondeu para session_id: {query.session_id}. Resposta: '{response.get('output', '')[:100]}...'")

        # Atualiza o histórico com a pergunta atual e a resposta do agente
        session_histories[query.session_id].append({"type": "human", "content": query.question})
        session_histories[query.session_id].append({"type": "ai", "content": response.get("output", "")})

        return {"response": response.get("output", "")}
    except Exception as e:
        logger.error(f"Erro ao invocar o agente para session_id {query.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request: {e}")
