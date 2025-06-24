# agents.py
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser # Importação adicionada
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
    "verification": config.get_llm("verification_agent") # .bind_tools removido pois o OutputFixingParser não lida bem com tools na LLM diretamente
}

async def run_anamnesis_agent(state):
    print("---EXECUTANDO AGENTE DE ANAMNESE---")
    anamnesis_llm = llms["anamnesis"]
    parser = PydanticOutputParser(pydantic_object=StructuredPatientData)
    output_fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=anamnesis_llm)

    prompt_template = ChatPromptTemplate.from_template(
        ANAMNESIS_PROMPT + "\n\n{format_instructions}",
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt_template | anamnesis_llm

    try:
        response = await config.throttled_google_acall(chain, {"patient_data": state['patient_data']})
        structured_data = parser.parse(response.content)
    except Exception as e:
        logging.warning(f"Falha no parsing inicial do agente de anamnese: {e}. Tentando corrigir...")
        try:
            # A resposta do LLM está em response.content
            structured_data = output_fixing_parser.parse(response.content)
            logging.info("Parsing corrigido com sucesso pelo OutputFixingParser.")
        except Exception as e_fix:
            logging.error(f"Falha ao corrigir o parsing do agente de anamnese: {e_fix}")
            # Retorna um estado de erro ou um dicionário indicando a falha
            return {"patient_data_structured": None, "error_anamnesis": str(e_fix)}

    if structured_data:
        kb_manager.add_patient_data(state['patient_id'], structured_data.dict())
        return {"patient_data_structured": structured_data.dict()}
    else: # Caso OutputFixingParser também não consiga (embora ele tenda a levantar exceção)
        return {"patient_data_structured": None, "error_anamnesis": "Falha no parsing e na correção."}

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
    verification_llm = llms["verification"] # LLM para o agente
    parser = PydanticOutputParser(pydantic_object=VerificationResult)
    # O OutputFixingParser precisa de um LLM para tentar corrigir a saída
    output_fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=verification_llm)

    prompt_template = ChatPromptTemplate.from_template(
        VERIFICATION_PROMPT + "\n\n{format_instructions}",
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    # A cadeia agora é prompt -> llm. O parser é aplicado depois.
    chain = prompt_template | verification_llm

    try:
        response = await config.throttled_google_acall(chain, {"plan": state['plan']})
        # Tentativa de parsing inicial
        verification_result = parser.parse(response.content)
    except Exception as e:
        logging.warning(f"Falha no parsing inicial do agente de verificação: {e}. Tentando corrigir...")
        try:
            # Tenta corrigir usando OutputFixingParser
            # A resposta do LLM (string) está em response.content
            verification_result = output_fixing_parser.parse(response.content)
            logging.info("Parsing corrigido com sucesso pelo OutputFixingParser para verificação.")
        except Exception as e_fix:
            logging.error(f"Falha ao corrigir o parsing do agente de verificação: {e_fix}")
            # Retorna um estado de erro ou um dicionário indicando a falha
            return {"verification": {"is_safe_to_proceed": False, "notes": f"Erro de parsing: {e_fix}", "confidence_score": 0.0, "error_verification": str(e_fix)}}

    if verification_result:
        return {"verification": verification_result.dict()}
    else: # Caso OutputFixingParser também não consiga
        return {"verification": {"is_safe_to_proceed": False, "notes": "Falha no parsing e na correção da verificação.", "confidence_score": 0.0, "error_verification": "Falha no parsing e na correção."}}
