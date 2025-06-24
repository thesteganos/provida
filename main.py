
**Arquivo: `main.py`**```python
# main.py
import os
import shutil
import uuid
import langchain
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/ingest")
async def ingest_new_knowledge(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido.")
    upload_dir = os.path.join("knowledge_sources", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")
    background_tasks.add_task(kb_manager.ingest_new_document, file_path=file_path)
    return {"message": f"Arquivo '{file.filename}' recebido para ingestão em segundo plano."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
