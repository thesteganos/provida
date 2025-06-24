# agents.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser

from prompts import ANAMNESIS_PROMPT, DIAGNOSIS_PROMPT, PLANNING_PROMPT, VERIFICATION_PROMPT
from tools import patient_kg_query_tool, rag_evidence_search_tool
from kb_manager import kb_manager
# Importa o nosso carregador de configuração
from config_loader import config

# --- LLMs são carregados dinamicamente com base na configuração ---

def run_anamnesis_agent(state):
    print("---EXECUTANDO AGENTE DE ANAMNESE---")
    llm = config.get_llm("anamnesis_agent")
    patient_data = state['patient_data']
    prompt = ChatPromptTemplate.from_template(ANAMNESIS_PROMPT)
    chain = prompt | llm | JsonOutputParser()
    structured_data = chain.invoke({"patient_data": patient_data})
    kb_manager.add_patient_data(state['patient_id'], structured_data)
    return {"patient_data_structured": structured_data}

def run_diagnosis_agent(state):
    print("---EXECUTANDO AGENTE DE DIAGNÓSTICO---")
    llm = config.get_llm("diagnosis_agent")
    llm_with_tools = llm.bind_tools([patient_kg_query_tool])
    prompt = ChatPromptTemplate.from_template(DIAGNOSIS_PROMPT)
    chain = prompt | llm_with_tools
    result = chain.invoke({"patient_id": state['patient_id']})
    diagnosis = result.content
    return {"diagnosis": diagnosis}

def run_planning_agent(state):
    print("---EXECUTANDO AGENTE DE PLANEJAMENTO TERAPÊUTICO---")
    llm = config.get_llm("planning_agent")
    llm_with_tools = llm.bind_tools([rag_evidence_search_tool])
    prompt = ChatPromptTemplate.from_template(PLANNING_PROMPT)
    chain = prompt | llm_with_tools
    result = chain.invoke({
        "diagnosis": state['diagnosis'],
        "patient_data": state['patient_data_structured']
    })
    plan = result.content
    return {"plan": plan}

def run_verification_agent(state):
    print("---EXECUTANDO AGENTE DE VERIFICAÇÃO---")
    llm = config.get_llm("verification_agent")
    llm_with_tools = llm.bind_tools([rag_evidence_search_tool])
    prompt = ChatPromptTemplate.from_template(VERIFICATION_PROMPT)
    chain = prompt | llm_with_tools | JsonOutputParser()
    verification_result = chain.invoke({"plan": state['plan']})
    return {"verification": verification_result}
