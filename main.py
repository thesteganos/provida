# main.py
import uuid
from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from graph import provida_app, AgentState

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Instância da API FastAPI
app = FastAPI(
    title="PROVIDA - Ecossistema de IA para Gestão Metabólica",
    description="Uma API para iniciar o processo de análise e planejamento para um paciente.",
    version="1.0.0"
)

# Modelos de dados para a API (validação de entrada/saída)
class PatientInput(BaseModel):
    name: str = "João da Silva"
    age: int = 45
    imc: float = 34.0
    hba1c: float = 6.8
    notes: str = "Paciente relata cansaço frequente e aumento da sede."

class ProcessResponse(BaseModel):
    patient_id: str
    final_plan_for_clinician: str

@app.post("/process_patient", response_model=ProcessResponse)
def process_patient_data(patient_input: PatientInput):
    """
    Endpoint para processar os dados de um novo paciente e gerar um plano terapêutico.
    """
    patient_id = str(uuid.uuid4())
    
    initial_state: AgentState = {
        "patient_id": patient_id,
        "patient_data": patient_input.dict(),
        "patient_data_structured": None,
        "diagnosis": None,
        "plan": None,
        "verification": None,
        "final_response": None
    }
    
    # Invoca o workflow do LangGraph
    final_state = provida_app.invoke(initial_state)
    
    return ProcessResponse(
        patient_id=patient_id,
        final_plan_for_clinician=final_state.get("final_response", "Erro no processamento.")
    )

if __name__ == "__main__":
    import uvicorn
    # Para rodar: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
