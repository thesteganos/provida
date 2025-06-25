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
import langchain
import logging # Adicionado logging
from fastapi import FastAPI, UploadFile, File, HTTPException # BackgroundTasks removido
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_community.cache import InMemoryCache

load_dotenv()
langchain.llm_cache = InMemoryCache()

from graph import provida_app
from kb_manager import kb_manager

app = FastAPI(title="PROVIDA - Ecossistema de IA para Gestão Metabólica", version="2.0.0")

class PatientInput(BaseModel):
    """Modelo Pydantic para os dados de entrada de um paciente."""
    name: str = Field(..., example="João da Silva", description="Nome completo do paciente.")
    age: int = Field(..., example=45, description="Idade do paciente em anos.")
    imc: float = Field(..., example=34.0, description="Índice de Massa Corporal (IMC) do paciente.")
    hba1c: float = Field(..., example=6.8, description="Valor da Hemoglobina Glicada (HbA1c) do paciente.")
    notes: str = Field(..., example="Paciente relata cansaço frequente.", description="Notas clínicas adicionais ou queixas do paciente.")

class ProcessRequest(BaseModel):
    """Modelo Pydantic para a requisição de processamento de paciente."""
    patient_id: Optional[str] = Field(None, description="ID existente do paciente (opcional). Se não fornecido, um novo ID será gerado.")
    patient_data: PatientInput = Field(..., description="Dados do paciente para processamento.")

class ProcessResponse(BaseModel):
    """Modelo Pydantic para a resposta do processamento de paciente."""
    patient_id: str = Field(..., description="ID do paciente processado.")
    final_plan_for_clinician: str = Field(..., description="Plano terapêutico final gerado para o clínico.")

class KnowledgeQuery(BaseModel):
    """Modelo Pydantic para a requisição de consulta à base de conhecimento."""
    query: str = Field(..., description="Texto da pergunta ou tópico para buscar na base de conhecimento RAG.")

class DocumentMetadata(BaseModel):
    """Modelo Pydantic para os metadados de um trecho de documento."""
    source: str = Field(..., description="Origem do documento (ex: nome do arquivo).")
    page: Optional[int] = Field(None, description="Número da página (se aplicável).")

class DocumentSnippet(BaseModel):
    """Modelo Pydantic para um trecho de documento recuperado pela busca RAG."""
    page_content: str = Field(..., description="Conteúdo textual do trecho do documento.")
    metadata: DocumentMetadata = Field(..., description="Metadados associados ao trecho.")

class KnowledgeResponse(BaseModel):
    """Modelo Pydantic para a resposta da consulta à base de conhecimento."""
    source_documents: list[DocumentSnippet] = Field(..., description="Lista de trechos de documentos relevantes encontrados.")

@app.post("/process_patient", response_model=ProcessResponse, summary="Processa Dados do Paciente e Gera Plano Terapêutico")
async def process_patient_data(request: ProcessRequest):
    """
    Recebe os dados de um paciente, executa o fluxo de agentes PROVIDA e retorna um plano terapêutico.

    - Se `patient_id` não for fornecido na requisição, um novo UUID é gerado.
    - Invoca o `provida_app` (grafo LangGraph) com o estado inicial contendo
      `patient_id` e `patient_data`.
    - Retorna o ID do paciente e o plano final gerado.
    """
    patient_id = request.patient_id or str(uuid.uuid4())
    initial_state = {"patient_id": patient_id, "patient_data": request.patient_data.dict()}
    try:
        final_state = await provida_app.ainvoke(initial_state)
        return ProcessResponse(patient_id=patient_id, final_plan_for_clinician=final_state.get("final_response", "Erro no processamento."))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no fluxo do agente: {e}")

@app.post("/knowledge/query", response_model=KnowledgeResponse, summary="Consulta a Base de Conhecimento RAG")
async def query_knowledge_base(query: KnowledgeQuery):
    """
    Realiza uma busca na base de conhecimento RAG (documentos) com a query fornecida.

    - Utiliza o retriever do `kb_manager` para encontrar trechos de documentos relevantes.
    - Retorna uma lista de `DocumentSnippet` contendo o conteúdo e metadados dos trechos.
    """
    try:
        docs = await kb_manager.retriever.ainvoke(query.query)
        return KnowledgeResponse(source_documents=[DocumentSnippet.model_validate(doc.dict()) for doc in docs])
    except Exception as e:
        logging.error(f"Erro ao consultar a base de conhecimento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/ingest", summary="Ingere Novo Documento na Base de Conhecimento")
async def ingest_new_knowledge(file: UploadFile = File(...)):
    """
    Recebe um arquivo (PDF ou TXT) via upload e o ingere na base de conhecimento RAG.

    - Valida o tipo de arquivo (somente .pdf e .txt são permitidos).
    - Salva o arquivo temporariamente em `knowledge_sources/uploads`.
    - Chama `kb_manager.ingest_new_document()` para processar e indexar o documento.
    - Retorna uma mensagem com o resultado da ingestão.
    - Lida com possíveis erros durante o salvamento e a ingestão, retornando HTTPExceptions apropriadas.
    """
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Apenas PDF e TXT são permitidos.")

    upload_dir = os.path.join("knowledge_sources", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"Arquivo '{file.filename}' salvo em '{file_path}'.")
    except Exception as e:
        logging.error(f"Não foi possível salvar o arquivo '{file.filename}' em '{file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    try:
        # Chamada síncrona para ingestão
        ingestion_result = kb_manager.ingest_new_document(file_path=file_path)
        logging.info(f"Resultado da ingestão para '{file.filename}': {ingestion_result}")

        # Verificar se o resultado indica algum tipo de erro ou aviso tratável
        if "erro" in ingestion_result.lower() or "falha" in ingestion_result.lower() or "não encontrado" in ingestion_result.lower():
            # Considerar um erro 4xx se for um problema com o arquivo em si, ou 5xx se for falha interna
            raise HTTPException(status_code=422, detail=f"Processamento do documento '{file.filename}' resultou em: {ingestion_result}")

        if "duplicado" in ingestion_result.lower() or "já existe" in ingestion_result.lower():
             # Isso não é necessariamente um erro do servidor, mas uma condição do arquivo.
             # Um status 200 com uma mensagem clara, ou um 202 Accepted, ou 409 Conflict podem ser apropriados.
             # Usando 200 com mensagem detalhada.
            return {"message": f"Arquivo '{file.filename}' processado.", "detail": ingestion_result}

        return {"message": f"Arquivo '{file.filename}' ingerido com sucesso.", "detail": ingestion_result}
    except HTTPException as http_exc: # Repassa HTTPExceptions
        raise http_exc
    except Exception as e:
        logging.error(f"Erro durante a ingestão do documento '{file.filename}': {e}", exc_info=True)
        # Remove o arquivo se a ingestão falhou para evitar reprocessamento automático se não desejado.
        # os.remove(file_path) # Descomentar se este for o comportamento desejado.
        raise HTTPException(status_code=500, detail=f"Erro interno durante a ingestão do documento: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
