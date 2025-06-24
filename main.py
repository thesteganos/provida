
**Arquivo: `main.py`**```python
# main.py
import os
import shutil
import uuid
import langchain
import logging # Adicionado logging
from fastapi import FastAPI, UploadFile, File, HTTPException # BackgroundTasks removido
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.cache import InMemoryCache

load_dotenv()
langchain.llm_cache = InMemoryCache()

from graph import provida_app
from kb_manager import kb_manager

app = FastAPI(title="PROVIDA - Ecossistema de IA para Gestão Metabólica", version="2.0.0")

class PatientInput(BaseModel):
    name: str = Field(..., example="João da Silva")
    age: int = Field(..., example=45)
    imc: float = Field(..., example=34.0)
    hba1c: float = Field(..., example=6.8)
    notes: str = Field(..., example="Paciente relata cansaço frequente.")

class ProcessRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="ID existente do paciente.")
    patient_data: PatientInput

class ProcessResponse(BaseModel):
    patient_id: str
    final_plan_for_clinician: str

class KnowledgeQuery(BaseModel): query: str
class DocumentMetadata(BaseModel): source: str; page: Optional[int] = None
class DocumentSnippet(BaseModel): page_content: str; metadata: DocumentMetadata
class KnowledgeResponse(BaseModel): source_documents: list[DocumentSnippet]

@app.post("/process_patient", response_model=ProcessResponse)
async def process_patient_data(request: ProcessRequest):
    patient_id = request.patient_id or str(uuid.uuid4())
    initial_state = {"patient_id": patient_id, "patient_data": request.patient_data.dict()}
    try:
        final_state = await provida_app.ainvoke(initial_state)
        return ProcessResponse(patient_id=patient_id, final_plan_for_clinician=final_state.get("final_response", "Erro no processamento."))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no fluxo do agente: {e}")

@app.post("/knowledge/query", response_model=KnowledgeResponse)
async def query_knowledge_base(query: KnowledgeQuery):
    try:
        docs = await kb_manager.retriever.ainvoke(query.query)
        return KnowledgeResponse(source_documents=[DocumentSnippet.model_validate(doc.dict()) for doc in docs])
    except Exception as e:
        logging.error(f"Erro ao consultar a base de conhecimento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/ingest")
async def ingest_new_knowledge(file: UploadFile = File(...)): # Removido BackgroundTasks
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
