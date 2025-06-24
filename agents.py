# agents.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser

from prompts import ANAMNESIS_PROMPT, DIAGNOSIS_PROMPT, PLANNING_PROMPT, VERIFICATION_PROMPT
from tools import patient_kg_query_tool, rag_evidence_search_tool
from kb_manager import kb_manager

# Modelo Gemini que será usado por todos os agentes
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.2)

def run_anamnesis_agent(state):
    """Estrutura os dados iniciais do paciente."""
    print("---EXECUTANDO AGENTE DE ANAMNESE---")
    patient_data = state['patient_data']
    
    prompt = ChatPromptTemplate.from_template(ANAMNESIS_PROMPT)
    chain = prompt | llm | JsonOutputParser()
    
    structured_data = chain.invoke({"patient_data": patient_data})
    
    # Adiciona ao KG do Paciente
    kb_manager.add_patient_data(state['patient_id'], structured_data)
    
    return {"patient_data_structured": structured_data}

def run_diagnosis_agent(state):
    """Analisa os dados e gera um diagnóstico/resumo de riscos."""
    print("---EXECUTANDO AGENTE DE DIAGNÓSTICO---")
    llm_with_tools = llm.bind_tools([patient_kg_query_tool])
    prompt = ChatPromptTemplate.from_template(DIAGNOSIS_PROMPT)
    
    chain = prompt | llm_with_tools
    
    result = chain.invoke({"patient_id": state['patient_id']})
    # Simplificado: assumimos que o conteúdo da mensagem é o diagnóstico
    diagnosis = result.content
    
    return {"diagnosis": diagnosis}

def run_planning_agent(state):
    """Cria o plano terapêutico com base no diagnóstico."""
    print("---EXECUTANDO AGENTE DE PLANEJAMENTO TERAPÊUTICO---")
    llm_with_tools = llm.bind_tools([rag_evidence_search_tool])
    prompt = ChatPromptTemplate.from_template(PLANNING_PROMPT)
    
    chain = prompt | llm_with_tools
    
    result = chain.invoke({
        "diagnosis": state['diagnosis'],
        "patient_data": state['patient_data_structured']
    })
    plan = result.content # Simplificado
    
    return {"plan": plan}

def run_verification_agent(state):
    """Verifica o plano proposto e atribui um score de confiança."""
    print("---EXECUTANDO AGENTE DE VERIFICAÇÃO---")
    llm_with_tools = llm.bind_tools([rag_evidence_search_tool])
    prompt = ChatPromptTemplate.from_template(VERIFICATION_PROMPT)
    
    chain = prompt | llm_with_tools | JsonOutputParser()
    
    verification_result = chain.invoke({"plan": state['plan']})
    
    return {"verification": verification_result}
