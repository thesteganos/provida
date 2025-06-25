# main.py
"""
Este módulo implementa a API FastAPI para a aplicação PROVIDA.

Ele define os endpoints para:
1. Processar dados de pacientes: Recebe informações do paciente, dispara o fluxo
   de agentes (definido em `graph.py`) e retorna o plano terapêutico final.
2. Consultar a base de conhecimento: Permite realizar buscas RAG na base de
   documentos (gerenciada por `kb_manager.py`).
3. Ingerir novos documentos: Permite o upload de arquivos PDF ou TXT para
   serem adicionados à base de conhecimento RAG.

Utiliza Pydantic para validação de dados de requisição e resposta.
Carrega variáveis de ambiente com `dotenv` e configura um cache em memória
para LLMs com LangChain.
"""
import os
import shutil
import uuid
import re # Para sanitizar nomes de arquivo
import langchain
import logging
from typing import Optional, List, Dict, Any # Adicionado para type hints
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_community.cache import InMemoryCache
from langchain_core.documents import Document as LangchainDocument # Para type hint

load_dotenv()
langchain.llm_cache = InMemoryCache()
logger = logging.getLogger(__name__) # Configurar logger para o módulo

from graph import provida_app, AgentState # AgentState para tipagem se necessário
from kb_manager import kb_manager

# Configuração de logging básica (pode ser mais elaborada em um arquivo de config de logging)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


app = FastAPI(
    title="PROVIDA - Ecossistema de IA para Gestão Metabólica",
    version="2.0.1", # Versão atualizada
    description="API para interagir com o sistema PROVIDA, incluindo processamento de pacientes, consulta à base de conhecimento e ingestão de novos documentos."
)

# --- Modelos Pydantic para Requisições e Respostas ---

class PatientInput(BaseModel):
    """Modelo Pydantic para os dados de entrada de um paciente."""
    name: str = Field(..., min_length=1, example="João da Silva", description="Nome completo do paciente.")
    age: int = Field(..., gt=0, example=45, description="Idade do paciente em anos.")
    imc: float = Field(..., gt=0, example=34.0, description="Índice de Massa Corporal (IMC) do paciente.")
    hba1c: float = Field(..., gt=0, example=6.8, description="Valor da Hemoglobina Glicada (HbA1c) do paciente.")
    notes: str = Field(default="", example="Paciente relata cansaço frequente.", description="Notas clínicas adicionais ou queixas do paciente.")

class ProcessRequest(BaseModel):
    """Modelo Pydantic para a requisição de processamento de paciente."""
    patient_id: Optional[str] = Field(None, example=str(uuid.uuid4()), description="ID existente do paciente (opcional). Se não fornecido, um novo ID será gerado.")
    patient_data: PatientInput = Field(..., description="Dados do paciente para processamento.")

class ProcessResponse(BaseModel):
    """Modelo Pydantic para a resposta do processamento de paciente."""
    patient_id: str = Field(..., description="ID do paciente processado.")
    final_plan_for_clinician: str = Field(..., description="Plano terapêutico final gerado para o clínico.")

class KnowledgeQueryRequest(BaseModel): # Renomeado para evitar conflito com tipo interno
    """Modelo Pydantic para a requisição de consulta à base de conhecimento."""
    query: str = Field(..., min_length=1, description="Texto da pergunta ou tópico para buscar na base de conhecimento RAG.")

class DocumentMetadata(BaseModel):
    """Modelo Pydantic para os metadados de um trecho de documento."""
    source: str = Field(..., description="Origem do documento (ex: nome do arquivo).")
    page: Optional[int] = Field(None, description="Número da página (se aplicável).")

class DocumentSnippet(BaseModel):
    """Modelo Pydantic para um trecho de documento recuperado pela busca RAG."""
    page_content: str = Field(..., description="Conteúdo textual do trecho do documento.")
    metadata: DocumentMetadata = Field(..., description="Metadados associados ao trecho.")

class KnowledgeQueryResponse(BaseModel): # Renomeado para evitar conflito
    """Modelo Pydantic para a resposta da consulta à base de conhecimento."""
    source_documents: List[DocumentSnippet] = Field(..., description="Lista de trechos de documentos relevantes encontrados.")

class IngestResponse(BaseModel):
    """Modelo Pydantic para a resposta da ingestão de documentos."""
    message: str
    detail: str
    filename: Optional[str] = None


# --- Endpoints da API ---

@app.post(
    "/process_patient",
    response_model=ProcessResponse,
    summary="Processa Dados do Paciente e Gera Plano Terapêutico",
    tags=["Paciente"]
)
async def process_patient_data_endpoint(request: ProcessRequest):
    """
    Recebe os dados de um paciente, executa o fluxo de agentes PROVIDA e retorna um plano terapêutico.

    - Se `patient_id` não for fornecido na requisição, um novo UUID é gerado.
    - Invoca o `provida_app` (grafo LangGraph) com o estado inicial.
    - Retorna o ID do paciente e o plano final gerado.
    """
    patient_id = request.patient_id or str(uuid.uuid4())
    logger.info(f"Iniciando processamento para paciente ID: {patient_id}")

    initial_state: AgentState = {
        "patient_id": patient_id,
        "patient_data": request.patient_data.model_dump(), # Usar model_dump() para Pydantic v2
        "patient_data_structured": None,
        "diagnosis": None,
        "plan": None,
        "verification": None,
        "replan_instructions": None,
        "final_response": None,
        "error_anamnesis": None,
        "error_diagnosis": None,
        "error_planning": None,
        "error_verification": None,
        "warning_anamnesis": None,
    }

    try:
        # Timeout pode ser considerado para chamadas ainvoke muito longas
        final_state = await provida_app.ainvoke(initial_state, {"recursion_limit": 10})

        response_plan = final_state.get("final_response")
        if response_plan is None:
            logger.error(f"Processamento para {patient_id} concluído, mas 'final_response' está ausente no estado final.")
            # Isso pode indicar um erro no design do grafo ou um caminho inesperado.
            # A resposta do `finalize_response` no grafo já deve incluir detalhes do erro.
            # Se ainda assim for None, é um problema mais sério.
            response_plan = "Erro crítico: A resposta final não pôde ser gerada. Verifique os logs do servidor."
            # Não levanta HTTPException aqui para ainda retornar o patient_id e o erro no corpo.
            # O cliente verá o erro na string.

        logger.info(f"Processamento para paciente ID: {patient_id} concluído.")
        return ProcessResponse(patient_id=patient_id, final_plan_for_clinician=response_plan)

    except Exception as e:
        logger.error(f"Erro crítico no fluxo do agente para patient_id {patient_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor durante o processamento do paciente: {e}")

@app.post(
    "/knowledge/query",
    response_model=KnowledgeQueryResponse,
    summary="Consulta a Base de Conhecimento RAG",
    tags=["Conhecimento"]
)
async def query_knowledge_base_endpoint(request_data: KnowledgeQueryRequest):
    """
    Realiza uma busca na base de conhecimento RAG (documentos) com a query fornecida.
    """
    logger.info(f"Recebida consulta à base de conhecimento: '{request_data.query[:100]}...'")
    try:
        # kb_manager.retriever.ainvoke deve ser tipado corretamente se possível.
        # LangchainDocument é o tipo comum para documentos retornados por retrievers.
        docs: List[LangchainDocument] = await kb_manager.retriever.ainvoke(request_data.query)

        source_documents_response = []
        if docs:
            for doc in docs:
                # Converte metadados para o modelo Pydantic DocumentMetadata
                metadata_dict = {"source": doc.metadata.get("source", "Desconhecida")}
                if "page" in doc.metadata:
                    metadata_dict["page"] = doc.metadata["page"]

                source_documents_response.append(
                    DocumentSnippet(
                        page_content=doc.page_content,
                        metadata=DocumentMetadata(**metadata_dict)
                    )
                )
        logger.info(f"Consulta à base de conhecimento por '{request_data.query[:100]}...' retornou {len(source_documents_response)} documentos.")
        return KnowledgeQueryResponse(source_documents=source_documents_response)
    except Exception as e:
        logger.error(f"Erro ao consultar a base de conhecimento com query '{request_data.query[:100]}...': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno ao consultar a base de conhecimento: {e}")

def _sanitize_filename(filename: str) -> str:
    """Remove caracteres potencialmente perigosos ou problemáticos de um nome de arquivo."""
    if not filename: return "default_upload_name"
    # Remove caminhos (../, /)
    basename = os.path.basename(filename)
    # Substitui caracteres não alfanuméricos (exceto . _ -) por _
    sanitized_name = re.sub(r'[^\w.\-_]', '_', basename)
    # Limita o comprimento para evitar nomes de arquivo excessivamente longos
    return sanitized_name[:200]


@app.post(
    "/knowledge/ingest",
    response_model=IngestResponse,
    summary="Ingere Novo Documento na Base de Conhecimento",
    status_code=202, # Accepted: A requisição foi aceita para processamento.
    tags=["Conhecimento"]
)
async def ingest_new_knowledge_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Arquivo PDF ou TXT para ser ingerido.")
):
    """
    Recebe um arquivo (PDF ou TXT) e o adiciona à base de conhecimento RAG em background.
    Retorna uma resposta imediata.
    """
    original_filename = file.filename or "unknown_file"
    logger.info(f"Recebido arquivo '{original_filename}' para ingestão.")

    if not (original_filename.lower().endswith('.pdf') or original_filename.lower().endswith('.txt')):
        logger.warning(f"Tentativa de upload de arquivo com formato inválido: {original_filename}")
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Apenas PDF e TXT são permitidos.")

    upload_dir = os.path.join("knowledge_sources", "uploads_temp") # Diretório temporário
    os.makedirs(upload_dir, exist_ok=True)

    # Sanitiza o nome do arquivo e garante um nome único para evitar colisões
    sanitized_basename = _sanitize_filename(original_filename)
    unique_filename = f"{str(uuid.uuid4())}_{sanitized_basename}"
    file_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Arquivo '{original_filename}' salvo temporariamente como '{unique_filename}' em '{file_path}'.")
    except Exception as e:
        logger.error(f"Não foi possível salvar o arquivo '{original_filename}' em '{file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo no servidor: {e}")
    finally:
        if file.file: # Garante que o file object seja fechado
            file.file.close()

    # Adiciona a tarefa de ingestão em background
    # kb_manager.ingest_new_document é síncrono, então será executado em um thread do pool do BackgroundTasks
    background_tasks.add_task(kb_manager.ingest_new_document, file_path=file_path)
    # Nota: O arquivo em file_path será processado. Se a ingestão for bem-sucedida,
    # o kb_manager pode movê-lo ou o research_worker (se configurado) pode pegá-lo.
    # Se a ingestão falhar, o arquivo temporário pode precisar ser limpo por outro mecanismo.
    # Por ora, o arquivo permanece em uploads_temp.

    logger.info(f"Tarefa de ingestão para '{original_filename}' (salvo como '{unique_filename}') agendada em background.")
    return IngestResponse(
        message=f"Arquivo '{original_filename}' recebido e agendado para ingestão.",
        detail="O processamento ocorrerá em segundo plano. O status final não é refletido nesta resposta.",
        filename=original_filename
    )


if __name__ == "__main__":
    # Configuração de logging para execução local com Uvicorn
    # Em produção, isso pode ser gerenciado por Gunicorn ou outro processo.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
    )
    logger.info("Iniciando servidor FastAPI com Uvicorn...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
