# agents.py
"""
Este módulo define os agentes de inteligência artificial que compõem o sistema PROVIDA.

Cada agente é especializado em uma tarefa específica dentro do fluxo de processamento
de dados do paciente, desde a anamnese até a verificação do plano terapêutico.
Os agentes utilizam modelos de linguagem (LLMs) configurados e podem interagir
com ferramentas para buscar informações ou realizar ações específicas.

Principais componentes:
- Modelos Pydantic para estruturação de dados de entrada e saída dos agentes.
- LLMs configurados para cada agente, obtidos através do `config_loader`.
- Funções assíncronas que representam a lógica de execução de cada agente.
- Integração com o `kb_manager` para persistir dados do paciente.
- Uso de parsers e output fixers para garantir a robustez da saída dos LLMs.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain.output_parsers import OutputFixingParser
from langchain_core.messages import BaseMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent

from prompts import ANAMNESIS_PROMPT, DIAGNOSIS_PROMPT, PLANNING_PROMPT, VERIFICATION_PROMPT
from tools import patient_kg_query_tool, rag_evidence_search_tool
from config_loader import config

logger = logging.getLogger(__name__)

StateType = Dict[str, Any]

class StructuredPatientData(BaseModel):
    """
    Modelo de dados para estruturar as informações do paciente coletadas na anamnese.
    """
    name: str = Field(description="Nome do paciente")
    age: int = Field(description="Idade do paciente")
    imc: float = Field(description="Índice de Massa Corporal")
    hba1c: float = Field(description="Valor da Hemoglobina Glicada")
    notes: str = Field(description="Notas clínicas ou queixas do paciente")

class VerificationResult(BaseModel):
    """
    Modelo de dados para estruturar o resultado da verificação do plano terapêutico.
    """
    confidence_score: float = Field(description="Score de confiança de 0.0 a 1.0 para o plano.", ge=0.0, le=1.0)
    notes: str = Field(description="Notas e justificativa da verificação.")
    is_safe_to_proceed: bool = Field(description="True se o plano for seguro, False caso contrário.")

class AgentState(BaseModel):
    """
    Representa o estado do agente durante a execução. (Versão Pydantic para validação)
    """
    input: str
    chat_history: List[BaseMessage] = Field(
        ...,
        extra={"is_chat_history": True}
    )

try:
    llms = {
        "anamnesis": config.get_llm("anamnesis_agent"),
        "diagnosis": config.get_llm("diagnosis_agent").bind_tools([patient_kg_query_tool]),
        "planning": config.get_llm("planning_agent").bind_tools([rag_evidence_search_tool]),
        "verification": config.get_llm("verification_agent")
    }
except ValueError as e:
    logger.critical(f"Erro crítico ao carregar LLMs configurados: {e}. A aplicação pode não funcionar corretamente.", exc_info=True)
    llms = {}

async def run_anamnesis_agent(state: StateType) -> StateType:
    """
    Executa o agente de anamnese para coletar e estruturar os dados iniciais do paciente.
    """
    from kb_manager import kb_manager
    
    logger.debug("---EXECUTANDO AGENTE DE ANAMNESE---")

    patient_data_raw = state.get('patient_data')
    patient_id = state.get('patient_id')

    if not patient_data_raw or not patient_id:
        logger.error("Dados do paciente brutos ou ID do paciente ausentes no estado para o agente de anamnese.")
        return {"patient_data_structured": None, "error_anamnesis": "Dados de entrada ausentes."}

    if not llms.get("anamnesis"):
        logger.error("LLM para agente de anamnese não está disponível.")
        return {"patient_data_structured": None, "error_anamnesis": "LLM não configurado."}

    anamnesis_llm = llms["anamnesis"]
    parser = PydanticOutputParser(pydantic_object=StructuredPatientData)
    output_fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=anamnesis_llm, max_retries=2)

    prompt_template = ChatPromptTemplate.from_template(
        ANAMNESIS_PROMPT + "\n\n{format_instructions}",
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt_template | anamnesis_llm

    try:
        response = await config.throttled_google_acall(chain, {"patient_data": patient_data_raw})
        structured_data = parser.parse(response.content)
        logger.info(f"Anamnese estruturada para paciente {patient_id} via parsing direto.")
    except OutputParserException as e_parse:
        logger.warning(f"Falha no parsing Pydantic inicial do agente de anamnese para {patient_id}: {e_parse}. Tentando corrigir...")
        try:
            structured_data = output_fixing_parser.parse(response.content)
            logger.info(f"Parsing da anamnese para {patient_id} corrigido com sucesso pelo OutputFixingParser.")
        except Exception as e_fix:
            logger.error(f"Falha ao corrigir o parsing do agente de anamnese para {patient_id}: {e_fix}", exc_info=True)
            return {"patient_data_structured": None, "error_anamnesis": f"Falha no parsing e na correção: {e_fix}"}
    except Exception as e_llm_call:
        logger.error(f"Erro na chamada LLM ou inesperado no agente de anamnese para {patient_id}: {e_llm_call}", exc_info=True)
        return {"patient_data_structured": None, "error_anamnesis": f"Erro na chamada LLM: {e_llm_call}"}

    if structured_data:
        try:
            if kb_manager:
                kb_manager.add_patient_data(patient_id, structured_data.dict())
                logger.info(f"Dados estruturados do paciente {patient_id} persistidos no KB.")
            else:
                 logger.error(f"kb_manager não pôde ser importado dentro de run_anamnesis_agent.")
                 return {"patient_data_structured": structured_data.dict(), "warning_anamnesis": "Dados estruturados mas falha ao importar KB Manager para salvar."}

            return {"patient_data_structured": structured_data.dict()}
        except Exception as e_kb:
            logger.error(f"Falha ao persistir dados da anamnese para {patient_id} no KB: {e_kb}", exc_info=True)
            return {"patient_data_structured": structured_data.dict(), "warning_anamnesis": f"Dados estruturados mas falha ao salvar no KB: {e_kb}"}
    else:
        logger.error(f"Agente de anamnese para {patient_id} não produziu dados estruturados mesmo após tentativa de correção.")
        return {"patient_data_structured": None, "error_anamnesis": "Falha no parsing e na correção (resultado final nulo)."}

async def run_diagnosis_agent(state: StateType) -> StateType:
    """
    Executa o agente de diagnóstico.
    """
    logger.debug("---EXECUTANDO AGENTE DE DIAGNÓSTICO---")
    patient_id = state.get('patient_id')
    if not patient_id:
        logger.error("ID do paciente ausente no estado para o agente de diagnóstico.")
        return {"diagnosis": None, "error_diagnosis": "ID do paciente ausente."}

    if not llms.get("diagnosis"):
        logger.error("LLM para agente de diagnóstico não está disponível.")
        return {"diagnosis": None, "error_diagnosis": "LLM não configurado."}

    prompt = ChatPromptTemplate.from_template(DIAGNOSIS_PROMPT)
    chain = prompt | llms["diagnosis"]

    try:
        result = await config.throttled_google_acall(chain, {"patient_id": patient_id})
        logger.info(f"Diagnóstico gerado para paciente {patient_id}.")
        return {"diagnosis": result.content}
    except Exception as e:
        logger.error(f"Erro ao executar agente de diagnóstico para {patient_id}: {e}", exc_info=True)
        return {"diagnosis": None, "error_diagnosis": f"Erro na execução do agente: {e}"}

async def run_planning_agent(state: StateType) -> StateType:
    """
    Executa o agente de planejamento terapêutico.
    """
    logger.debug("---EXECUTANDO AGENTE DE PLANEJAMENTO TERAPÊUTICO---")
    patient_id = state.get('patient_id')
    diagnosis = state.get('diagnosis')
    patient_data_structured = state.get('patient_data_structured')
    replan_instructions = state.get("replan_instructions", "Nenhuma instrução de replanejamento anterior.")

    if not diagnosis or not patient_data_structured:
        logger.error(f"Diagnóstico ou dados estruturados do paciente ausentes para planejamento (ID: {patient_id}).")
        return {"plan": None, "error_planning": "Dados de entrada insuficientes."}

    if not llms.get("planning"):
        logger.error(f"LLM para agente de planejamento não está disponível (ID: {patient_id}).")
        return {"plan": None, "error_planning": "LLM não configurado."}

    prompt = ChatPromptTemplate.from_template(PLANNING_PROMPT)
    chain = prompt | llms["planning"]

    try:
        result = await config.throttled_google_acall(chain, {
            "diagnosis": diagnosis,
            "patient_data": patient_data_structured,
            "replan_instructions": replan_instructions
        })
        logger.info(f"Plano terapêutico gerado para paciente {patient_id}.")
        return {"plan": result.content}
    except Exception as e:
        logger.error(f"Erro ao executar agente de planejamento para {patient_id}: {e}", exc_info=True)
        return {"plan": None, "error_planning": f"Erro na execução do agente: {e}"}

async def run_verification_agent(state: StateType) -> StateType:
    """
    Executa o agente de verificação para analisar a qualidade e segurança do plano terapêutico.
    """
    logger.debug("---EXECUTANDO AGENTE DE VERIFICAÇÃO---")
    plan_to_verify = state.get('plan')
    patient_id = state.get('patient_id')

    if not plan_to_verify:
        logger.error(f"Plano terapêutico ausente no estado para verificação (ID: {patient_id}).")
        return {"verification": VerificationResult(confidence_score=0.0, notes="Plano ausente para verificação.", is_safe_to_proceed=False).dict()}

    if not llms.get("verification"):
        logger.error(f"LLM para agente de verificação não está disponível (ID: {patient_id}).")
        return {"verification": VerificationResult(confidence_score=0.0, notes="LLM de verificação não configurado.", is_safe_to_proceed=False).dict()}

    verification_llm = llms["verification"]
    parser = PydanticOutputParser(pydantic_object=VerificationResult)
    output_fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=verification_llm, max_retries=2)

    prompt_template = ChatPromptTemplate.from_template(
        VERIFICATION_PROMPT + "\n\n{format_instructions}",
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt_template | verification_llm

    default_error_result = {
        "confidence_score": 0.0,
        "notes": "Falha crítica na verificação.",
        "is_safe_to_proceed": False
    }

    try:
        response = await config.throttled_google_acall(chain, {"plan": plan_to_verify})
        verification_result_obj = parser.parse(response.content)
        logger.info(f"Verificação do plano para {patient_id} concluída via parsing direto.")
    except OutputParserException as e_parse:
        logger.warning(f"Falha no parsing Pydantic inicial da verificação para {patient_id}: {e_parse}. Tentando corrigir...")
        try:
            verification_result_obj = output_fixing_parser.parse(response.content)
            logger.info(f"Parsing da verificação para {patient_id} corrigido com sucesso pelo OutputFixingParser.")
        except Exception as e_fix:
            logger.error(f"Falha ao corrigir o parsing da verificação para {patient_id}: {e_fix}", exc_info=True)
            return {"verification": {**default_error_result, "notes": f"Erro de parsing na verificação: {e_fix}"}}
    except Exception as e_llm_call:
        logger.error(f"Erro na chamada LLM ou inesperado no agente de verificação para {patient_id}: {e_llm_call}", exc_info=True)
        return {"verification": {**default_error_result, "notes": f"Erro na chamada LLM de verificação: {e_llm_call}"}}

    if verification_result_obj:
        return {"verification": verification_result_obj.dict()}
    else:
        logger.error(f"Agente de verificação para {patient_id} não produziu resultado estruturado mesmo após tentativa de correção.")
        return {"verification": {**default_error_result, "notes": "Falha no parsing e na correção da verificação (resultado final nulo)."}}
