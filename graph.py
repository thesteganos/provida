# graph.py
from typing import TypedDict, Dict, Any, Optional
from langgraph.graph import StateGraph, END

# Importa os agentes que serão os nós do nosso grafo
from agents import (
    run_anamnesis_agent,
    run_diagnosis_agent,
    run_planning_agent,
    run_verification_agent,
)

# --- Definição do Estado do Grafo ---
# O estado é um dicionário que flui entre os nós.
# Ele acumula os resultados de cada agente.
class AgentState(TypedDict):
    """
    Define a estrutura de dados para o estado compartilhado entre os agentes.
    
    Atributos:
        patient_id (str): Identificador único para o paciente.
        patient_data (Dict[str, Any]): Dados brutos de entrada sobre o paciente.
        patient_data_structured (Optional[Dict[str, Any]]): Dados do paciente após estruturação pelo agente de anamnese.
        diagnosis (Optional[str]): Resumo do diagnóstico e riscos gerado pelo agente de diagnóstico.
        plan (Optional[str]): O plano terapêutico gerado pelo agente de planejamento.
        verification (Optional[Dict[str, Any]]): O resultado da verificação do plano, incluindo score e notas.
        replan_instructions (Optional[str]): Instruções para o agente de planejamento caso um replanejamento seja necessário.
        final_response (Optional[str]): A resposta final consolidada para ser apresentada ao clínico.
    """
    patient_id: str
    patient_data: Dict[str, Any]
    patient_data_structured: Optional[Dict[str, Any]]
    diagnosis: Optional[str]
    plan: Optional[str]
    verification: Optional[Dict[str, Any]]
    replan_instructions: Optional[str]
    final_response: Optional[str]

# --- Nós de Lógica e Roteamento ---

def should_replan(state: AgentState) -> str:
    """
    Nó de roteamento condicional. Decide o próximo passo com base no resultado da verificação.
    
    Retorna:
        'finalize': Se o plano for considerado seguro e com alta confiança.
        'replan': Se o plano precisar de correções.
    """
    print("---ROTEANDO APÓS VERIFICAÇÃO---")
    verification_result = state.get("verification", {})
    is_safe = verification_result.get("is_safe_to_proceed", False)
    
    if is_safe:
        print("Plano verificado como seguro. Finalizando o fluxo.")
        return "finalize"
    else:
        print("Plano inseguro ou com baixa confiança. Enviando para replanejamento.")
        # Cria instruções claras para o próximo ciclo de planejamento
        replan_instructions = (
            "ATENÇÃO: O plano anterior foi rejeitado pela verificação de qualidade. "
            f"Notas da verificação: '{verification_result.get('notes', 'Nenhuma nota fornecida.')}'. "
            "Por favor, gere um novo plano de tratamento que corrija esses problemas específicos."
        )
        # Atualiza o estado com as instruções para o próximo nó
        state['replan_instructions'] = replan_instructions
        return "replan"

def finalize_response(state: AgentState) -> dict:
    """
    Nó final. Compila a resposta final e bem formatada para ser apresentada ao clínico.
    """
    print("---COMPILANDO RESPOSTA FINAL---")
    verification_result = state.get("verification", {})
    final_response = (
        f"## Plano Terapêutico Sugerido para o Paciente: {state['patient_id']} ##\n\n"
        f"**Diagnóstico e Riscos Avaliados:**\n{state.get('diagnosis', 'Não disponível.')}\n\n"
        f"**Plano Terapêutico Proposto:**\n{state.get('plan', 'Não disponível.')}\n\n"
        f"**Resultado da Verificação de Qualidade:**\n"
        f"  - Score de Confiança: {verification_result.get('confidence_score', 0.0):.2f}\n"
        f"  - Notas do Verificador: {verification_result.get('notes', 'N/A')}\n"
    )
    return {"final_response": final_response}

# --- Construção do Grafo de Workflow ---

print("Construindo o workflow de agentes com LangGraph...")

# Instancia o grafo com o estado definido
workflow = StateGraph(AgentState)

# Adiciona os nós ao grafo. Cada nó é uma função (um agente ou uma lógica de roteamento)
workflow.add_node("anamnesis", run_anamnesis_agent)
workflow.add_node("diagnosis", run_diagnosis_agent)
workflow.add_node("planning", run_planning_agent)
workflow.add_node("verification", run_verification_agent)
workflow.add_node("finalize", finalize_response)

# Define as arestas (conexões) que determinam o fluxo de execução
workflow.set_entry_point("anamnesis")
workflow.add_edge("anamnesis", "diagnosis")
workflow.add_edge("diagnosis", "planning")
workflow.add_edge("planning", "verification")
workflow.add_edge("finalize", END) # O nó END termina a execução do grafo

# Adiciona a aresta condicional para o ciclo de feedback
# A partir do nó 'verification', a função 'should_replan' será chamada.
# O retorno dessa função ('finalize' ou 'replan') determinará o próximo nó.
workflow.add_conditional_edges(
    "verification",
    should_replan,
    {
        "finalize": "finalize", # Se retornar 'finalize', vai para o nó 'finalize'
        "replan": "planning"    # Se retornar 'replan', volta para o nó 'planning'
    }
)

# Compila o grafo em um objeto executável que pode ser invocado
provida_app = workflow.compile()

print("Workflow de agentes compilado e pronto para uso.")
