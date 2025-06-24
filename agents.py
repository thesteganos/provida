# agents.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from prompts import ANAMNESIS_PROMPT, DIAGNOSIS_PROMPT, PLANNING_PROMPT, VERIFICATION_PROMPT
from tools import patient_kg_query_tool, rag_evidence_search_tool
from kb_manager import kb_manager
from config_loader import config

class StructuredPatientData(BaseModel):
    name: str = Field(description="Nome do paciente")
    age: int = Field(description="Idade do paciente")
    imc: float = Field(description="Índice de Massa Corporal")
    hba1c: float = Field(description="Valor da Hemoglobina Glicada")
    notes: str = Field(description="Notas clínicas ou queixas do paciente")

class VerificationResult(BaseModel):
    confidence_score: float = Field(description="Score de confiança de 0.0 a 1.0 para o plano.")
    notes: str = Field(description="Notas e justificativa da verificação.")
    is_safe_to_proceed: bool = Field(description="True se o plano for seguro, False caso contrário.")

llms = {
    "anamnesis": config.get_llm("anamnesis_agent"),
    "diagnosis": config.get_llm("diagnosis_agent").bind_tools([patient_kg_query_tool]),
    "planning": config.get_llm("planning_agent").bind_tools([rag_evidence_search_tool]),
    "verification": config.get_llm("verification_agent").bind_tools([rag_evidence_search_tool])
}

async def run_anamnesis_agent(state):
    print("---EXECUTANDO AGENTE DE ANAMNESE---")
    parser = PydanticOutputParser(pydantic_object=StructuredPatientData)
    prompt = ChatPromptTemplate.from_template(ANAMNESIS_PROMPT + "\n\n{format_instructions}", partial_variables={"format_instructions": parser.get_format_instructions()})
    chain = prompt | llms["anamnesis"] | parser
    structured_data = await config.throttled_google_acall(chain, {"patient_data": state['patient_data']})
    kb_manager.add_patient_data(state['patient_id'], structured_data.dict())
    return {"patient_data_structured": structured_data.dict()}

async def run_diagnosis_agent(state):
    print("---EXECUTANDO AGENTE DE DIAGNÓSTICO---")
    prompt = ChatPromptTemplate.from_template(DIAGNOSIS_PROMPT)
    chain = prompt | llms["diagnosis"]
    result = await config.throttled_google_acall(chain, {"patient_id": state['patient_id']})
    return {"diagnosis": result.content}

async def run_planning_agent(state):
    print("---EXECUTANDO AGENTE DE PLANEJAMENTO TERAPÊUTICO---")
    prompt = ChatPromptTemplate.from_template(PLANNING_PROMPT)
    chain = prompt | llms["planning"]
    result = await config.throttled_google_acall(chain, {
        "diagnosis": state['diagnosis'], "patient_data": state['patient_data_structured'], "replan_instructions": state.get("replan_instructions", "Nenhuma.")
    })
    return {"plan": result.content}

async def run_verification_agent(state):
    print("---EXECUTANDO AGENTE DE VERIFICAÇÃO---")
    parser = PydanticOutputParser(pydantic_object=VerificationResult)
    prompt = ChatPromptTemplate.from_template(VERIFICATION_PROMPT + "\n\n{format_instructions}", partial_variables={"format_instructions": parser.get_format_instructions()})
    chain = prompt | llms["verification"] | parser
    verification_result = await config.throttled_google_acall(chain, {"plan": state['plan']})
    return {"verification": verification_result.dict()}
