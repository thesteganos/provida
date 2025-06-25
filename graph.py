# graph.py
"""
Este módulo define e constrói o grafo de fluxo de trabalho (workflow) da aplicação PROVIDA.

Utilizando LangGraph, ele orquestra a execução sequencial e condicional dos diferentes
agentes (anamnese, diagnóstico, planejamento, verificação). O grafo gerencia o estado
da aplicação, passando informações entre os nós (agentes) e tomando decisões
de roteamento com base nos resultados intermediários.
"""
import logging
from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END, START # Importado START

# Importa os agentes que serão os nós do nosso grafo
from agents import (
    run_anamnesis_agent,
    run_diagnosis_agent,
    run_planning_agent,
    run_verification_agent,
)

logger = logging.getLogger(__name__)

# --- Definição do Estado do Grafo ---
class AgentState(TypedDict):
    """
    Define a estrutura de dados para o estado compartilhado entre os agentes.
    Todos os campos, exceto os de entrada inicial, são opcionais, pois são
    preenchidos incrementalmente ou podem falhar.
    """
    # Entradas Iniciais (obrigatórias ao iniciar o grafo)
    patient_id: str
    patient_data: Dict[str, Any]

    # Saídas dos Agentes (opcionais)
    patient_data_structured: Optional[Dict[str, Any]]
    diagnosis: Optional[str]
    plan: Optional[str]
    verification: Optional[Dict[str, Any]] # Contém is_safe_to_proceed, notes, confidence_score
    replan_instructions: Optional[str]
    final_response: Optional[str]

    # Campos de Erro/Aviso (para rastreamento e relatório)
    error_anamnesis: Optional[str]
    error_diagnosis: Optional[str]
    error_planning: Optional[str]
    error_verification: Optional[str]
    warning_anamnesis: Optional[str]
    # Adicionar mais campos de erro/aviso conforme necessário para outros agentes/etapas


# --- Nós de Lógica e Roteamento ---

def route_after_anamnesis(state: AgentState) -> str:
    """Decide para onde ir após a anamnese, baseado no sucesso da estruturação."""
    if state.get("error_anamnesis") or not state.get("patient_data_structured"):
        logger.warning(f"Erro ou falha na estruturação da anamnese para {state.get('patient_id')}. Pulando para finalização.")
        return "finalize" # Ou um nó de erro dedicado se preferir
    return "diagnosis"

def route_after_diagnosis(state: AgentState) -> str:
    """Decide para onde ir após o diagnóstico."""
    if state.get("error_diagnosis") or not state.get("diagnosis"):
        logger.warning(f"Erro ou ausência de diagnóstico para {state.get('patient_id')}. Pulando para finalização.")
        return "finalize" # Ou um nó de erro dedicado
    return "planning"

def route_after_planning(state: AgentState) -> str:
    """Decide para onde ir após o planejamento."""
    if state.get("error_planning") or not state.get("plan"):
        logger.warning(f"Erro ou ausência de plano para {state.get('patient_id')}. Pulando para finalização.")
        return "finalize" # Ou um nó de erro dedicado
    return "verification"


def should_replan_or_finalize(state: AgentState) -> str:
    """
    Decide se o fluxo de trabalho deve prosseguir para a finalização ou retornar ao planejamento.
    Esta função é chamada após o nó de verificação.
    """
    patient_id = state.get('patient_id', 'ID Desconhecido')
    logger.debug(f"---ROTEANDO APÓS VERIFICAÇÃO PARA PACIENTE {patient_id}---")
    
    verification_output = state.get("verification")

    # Caso 1: O próprio agente de verificação falhou em produzir uma saída estruturada ou reportou um erro interno.
    if not isinstance(verification_output, dict) or verification_output.get("error_verification"):
        logger.error(f"Falha crítica ou erro no agente de verificação para {patient_id}. Detalhes: {verification_output}")
        # Propaga o erro de verificação para o estado, se não já estiver lá por meio do próprio agente
        if isinstance(verification_output, dict) and verification_output.get("error_verification"):
            state['error_verification'] = verification_output.get("error_verification")
        else: # Caso não seja dict, ou não tenha a chave error_verification
            state['error_verification'] = state.get('error_verification', "Falha crítica na estrutura do resultado da verificação.")
        return "finalize" # Finaliza, pois não se pode confiar na verificação para replanejar.

    # Caso 2: A verificação foi concluída, mas o plano não é seguro ou precisa de ajustes.
    is_safe = verification_output.get("is_safe_to_proceed", False)
    if not isinstance(is_safe, bool): # Validação adicional
        logger.warning(f"'is_safe_to_proceed' com tipo inesperado ({type(is_safe)}) para {patient_id}. Tratando como False.")
        state['error_verification'] = (state.get('error_verification') or "") + " 'is_safe_to_proceed' com tipo inválido."
        is_safe = False

    if not is_safe: # Plano não seguro, precisa de replanejamento
        logger.info(f"Plano para {patient_id} inseguro ou com baixa confiança. Enviando para replanejamento.")
        notes_from_verification = verification_output.get('notes', 'Nenhuma nota de verificação fornecida.')
        replan_instructions = (
            "ATENÇÃO: O plano anterior foi rejeitado ou a verificação encontrou problemas. "
            f"Notas da verificação: '{notes_from_verification}'. "
            "Por favor, gere um novo plano de tratamento que corrija esses problemas."
        )
        state['replan_instructions'] = replan_instructions
        return "replan"

    # Caso 3: Plano verificado como seguro.
    logger.info(f"Plano para {patient_id} verificado como seguro. Finalizando o fluxo.")
    return "finalize"


def finalize_workflow_response(state: AgentState) -> Dict[str, Any]:
    """
    Compila a resposta final consolidada, incluindo erros e avisos de todas as etapas.
    Este é o nó final que prepara a saída do grafo.
    """
    patient_id = state.get('patient_id', 'ID Desconhecido')
    logger.debug(f"---COMPILANDO RESPOSTA FINAL PARA PACIENTE {patient_id}---")

    final_report_parts: List[str] = []
    final_report_parts.append(f"## Relatório Final para o Paciente: {patient_id} ##")

    # Coleta e formata erros e avisos de todas as etapas
    error_messages: List[str] = []
    warning_messages: List[str] = []

    if err_ana := state.get('error_anamnesis'): error_messages.append(f"Anamnese: {err_ana}")
    if warn_ana := state.get('warning_anamnesis'): warning_messages.append(f"Anamnese: {warn_ana}")
    if err_diag := state.get('error_diagnosis'): error_messages.append(f"Diagnóstico: {err_diag}")
    if err_plan := state.get('error_planning'): error_messages.append(f"Planejamento: {err_plan}")
    if err_verif := state.get('error_verification'): error_messages.append(f"Verificação: {err_verif}")
    # Adicionar mais conforme necessário

    if error_messages:
        final_report_parts.append("\n**Alertas Críticos Durante o Processamento:**")
        final_report_parts.extend([f"- {msg}" for msg in error_messages])
    if warning_messages:
        final_report_parts.append("\n**Avisos Durante o Processamento:**")
        final_report_parts.extend([f"- {msg}" for msg in warning_messages])

    # Informações principais (diagnóstico e plano)
    diagnosis_text = state.get('diagnosis', 'Diagnóstico não pôde ser gerado.')
    if state.get('error_diagnosis'): diagnosis_text += f" (Detalhe do erro: {state.get('error_diagnosis')})"
    final_report_parts.append(f"\n**Diagnóstico e Riscos Avaliados:**\n{diagnosis_text}")

    plan_text = state.get('plan', 'Plano terapêutico não pôde ser gerado.')
    if state.get('error_planning'): plan_text += f" (Detalhe do erro: {state.get('error_planning')})"
    final_report_parts.append(f"\n**Plano Terapêutico Proposto:**\n{plan_text}")

    # Resultado da Verificação
    verification_output = state.get("verification")
    if isinstance(verification_output, dict) and not verification_output.get("error_verification"):
        final_report_parts.append("\n**Resultado da Verificação de Qualidade:**")
        final_report_parts.append(f"  - Score de Confiança: {verification_output.get('confidence_score', 0.0):.2f}")
        final_report_parts.append(f"  - Notas do Verificador: {verification_output.get('notes', 'N/A')}")
        status_msg = "Seguro para prosseguir (segundo IA)." if verification_output.get('is_safe_to_proceed') else "Requer revisão ou não seguro para prosseguir."
        final_report_parts.append(f"  - Status: {status_msg}")
    elif state.get('error_verification'): # Se houve erro explícito na verificação
         final_report_parts.append(f"\n**Resultado da Verificação de Qualidade:**\n  - Falha na Verificação: {state['error_verification']}")
    else: # Se não houve erro explícito mas também não há resultado de verificação (ex: pulado)
        final_report_parts.append("\n**Resultado da Verificação de Qualidade:**\n  - Etapa de verificação não concluída ou pulada.")

    final_response_str = "\n\n".join(final_report_parts) # Adiciona mais espaço entre seções
    logger.info(f"Resposta final compilada para paciente {patient_id}.")
    # Atualiza o campo final_response no estado. O LangGraph retorna o estado final completo.
    state['final_response'] = final_response_str
    return state # Retorna o estado modificado, LangGraph lida com isso.


# --- Construção do Grafo de Workflow ---
logger.info("Construindo o workflow de agentes com LangGraph...")
workflow = StateGraph(AgentState)

# Adiciona os nós ao grafo
workflow.add_node("anamnesis", run_anamnesis_agent)
workflow.add_node("diagnosis", run_diagnosis_agent)
workflow.add_node("planning", run_planning_agent)
workflow.add_node("verification", run_verification_agent)
workflow.add_node("finalize_response_node", finalize_workflow_response) # Nó final para compilar a resposta

# Define o ponto de entrada
workflow.set_entry_point("anamnesis") # Ou pode usar START e adicionar uma aresta de START para anamnesis

# Define as arestas e roteamento condicional
# Se qualquer etapa crítica falhar, ela pode ser roteada diretamente para finalize_response_node

workflow.add_conditional_edges(
    "anamnesis",
    route_after_anamnesis,
    {"diagnosis": "diagnosis", "finalize": "finalize_response_node"}
)
workflow.add_conditional_edges(
    "diagnosis",
    route_after_diagnosis,
    {"planning": "planning", "finalize": "finalize_response_node"}
)
workflow.add_conditional_edges(
    "planning",
    route_after_planning,
    {"verification": "verification", "finalize": "finalize_response_node"}
)
workflow.add_conditional_edges(
    "verification",
    should_replan_or_finalize, # Nome da função de roteamento atualizada
    {"replan": "planning", "finalize": "finalize_response_node"}
)

# O nó 'finalize_response_node' é o último antes do fim.
workflow.add_edge("finalize_response_node", END)

# Compila o grafo
provida_app = workflow.compile()
logger.info("Workflow de agentes compilado e pronto para uso.")
