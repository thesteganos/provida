# graph.py
from typing import TypedDict, Dict, Any, Optional
from langgraph.graph import StateGraph, END
# Importa o nosso carregador de configuração para o estado inicial
from config_loader import config
from agents import (
    run_anamnesis_agent,
    run_diagnosis_agent,
    run_planning_agent,
    run_verification_agent,
)

# O AgentState permanece o mesmo
class AgentState(TypedDict):
    """Define o estado que flui através do grafo."""
    patient_id: str
    patient_data: Dict[str, Any]
    patient_data_structured: Optional[Dict[str, Any]]
    diagnosis: Optional[str]
    plan: Optional[str]
    verification: Optional[Dict[str, Any]]
    final_response: Optional[str]

# O restante do arquivo graph.py permanece exatamente o mesmo.
# A única diferença é que agora os agentes carregam seus próprios modelos
# internamente com base na configuração.

workflow = StateGraph(AgentState)
# ... (código do workflow inalterado) ...
workflow.add_node("anamnesis", run_anamnesis_agent)
workflow.add_node("diagnosis", run_diagnosis_agent)
workflow.add_node("planning", run_planning_agent)
workflow.add_node("verification", run_verification_agent)

workflow.set_entry_point("anamnesis")
workflow.add_edge("anamnesis", "diagnosis")
workflow.add_edge("diagnosis", "planning")
workflow.add_edge("planning", "verification")

def route_after_verification(state):
    print("---ROTEANDO APÓS VERIFICAÇÃO---")
    confidence_score = state["verification"].get("confidence_score", 0)
    
    if confidence_score > 0.8:
        print(f"Confiança alta ({confidence_score}). Finalizando.")
        final_response = (
            f"Plano gerado para o paciente {state['patient_id']}:\n\n"
            f"**Diagnóstico e Riscos:**\n{state['diagnosis']}\n\n"
            f"**Plano Terapêutico Proposto:**\n{state['plan']}\n\n"
            f"**Verificação:**\nConfiança de {state['verification']['confidence_score']:.2f}. "
            f"Notas: {state['verification']['notes']}"
        )
        state['final_response'] = final_response
        return "end"
    else:
        print(f"Confiança baixa ({confidence_score}). Finalizando com aviso.")
        final_response = (
            f"AVISO: O plano para o paciente {state['patient_id']} requer revisão manual.\n\n"
            f"**Verificação:**\nConfiança de {state['verification']['confidence_score']:.2f}. "
            f"Notas: {state['verification']['notes']}"
        )
        state['final_response'] = final_response
        return "end"

workflow.add_conditional_edges("verification", route_after_verification, {"end": END})

provida_app = workflow.compile()
