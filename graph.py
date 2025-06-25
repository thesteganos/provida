# graph.py
"""
Este módulo define o grafo de execução do sistema PROVIDA usando LangGraph.

O grafo define o fluxo de controle entre os diferentes agentes de IA.
Cada nó no grafo representa um agente (uma função que realiza uma tarefa),
e as arestas representam as transições condicionais entre eles, com base
no estado atual do processo.

Principais componentes:
- `AgentState`: Um dicionário tipado (TypedDict) que define a estrutura de dados
  do estado que é passado entre os nós do grafo.
- `TherapeuticWorkflowGraph`: Uma classe que encapsula a lógica de construção
  e execução do grafo LangGraph.
- Nós para cada agente: `run_anamnesis_agent`, `run_diagnosis_agent`, etc.
- Lógica de transição condicional (`decide_next_step`) que determina o
  próximo passo com base nos resultados do agente de verificação.
"""
import logging
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# A importação de 'agents' foi removida do topo para quebrar a dependência circular.
# A importação será feita dentro da função que a utiliza.

logger = logging.getLogger(__name__)

# Definição do estado do grafo usando TypedDict para clareza e verificação de tipos.
class AgentState(TypedDict):
    patient_id: str
    patient_data: str # Dados brutos iniciais
    patient_data_structured: dict # Dados após o agente de anamnese
    diagnosis: str # Resultado do agente de diagnóstico
    plan: str # Resultado do agente de planejamento
    verification: dict # Resultado (dicionário) do agente de verificação
    replan_instructions: Annotated[List[str], lambda x, y: x + y] # Acumula instruções de replanejamento

class TherapeuticWorkflowGraph:
    """
    Constrói e gerencia o grafo de fluxo de trabalho terapêutico com LangGraph.
    """
    def __init__(self):
        self.memory = MemorySaver()
        self.graph_app = self._build_graph()

    def _build_graph(self):
        """
        Define a estrutura do grafo, incluindo nós e arestas.
        """
        # A importação é feita aqui para garantir que os módulos já estejam carregados.
        from agents import (
            run_anamnesis_agent,
            run_diagnosis_agent,
            run_planning_agent,
            run_verification_agent
        )

        workflow = StateGraph(AgentState)

        # Adiciona os nós ao grafo, cada um correspondendo a um agente
        # MODIFICADO: Renomeando os nós para evitar conflito com as chaves do estado.
        workflow.add_node("anamnesis_step", run_anamnesis_agent)
        workflow.add_node("diagnosis_step", run_diagnosis_agent)
        workflow.add_node("planning_step", run_planning_agent)
        workflow.add_node("verification_step", run_verification_agent)

        # Define as arestas (fluxo de execução)
        # MODIFICADO: Apontando o ponto de entrada para o nome do nó correto.
        workflow.set_entry_point("anamnesis_step")
        
        # MODIFICADO: Atualizando as arestas com os novos nomes dos nós.
        workflow.add_edge("anamnesis_step", "diagnosis_step")
        workflow.add_edge("diagnosis_step", "planning_step")
        
        # A transição após a verificação é condicional
        # MODIFICADO: Atualizando a aresta condicional com os novos nomes dos nós.
        workflow.add_conditional_edges(
            "planning_step", # Começa no nó de planejamento
            self.prepare_for_verification, # Primeiro executa esta função
            {
                "replan": "planning_step", # Se precisar replanejar, volta para o planejamento
                "end": END # Se for seguro, termina o fluxo
            }
        )
        
        # Compila o grafo com o checkpointer para persistência de estado
        return workflow.compile(checkpointer=self.memory)

    def prepare_for_verification(self, state: AgentState) -> str:
        """
        Função intermediária que chama o agente de verificação e então decide o próximo passo.
        """
        # Importação local para garantir que o agente esteja disponível
        from agents import run_verification_agent
        
        # Roda a verificação como parte da lógica de transição
        # A verificação não precisa mais ser um nó explícito, pois é chamada aqui.
        # No entanto, a função do agente ainda é necessária.
        verification_result_state = run_verification_agent(state)
        state.update(verification_result_state) # Atualiza o estado com o resultado da verificação
        
        verification_data = state.get("verification", {})
        
        if verification_data.get("is_safe_to_proceed", False):
            logger.info(f"Verificação para paciente {state.get('patient_id')} aprovada. Finalizando fluxo.")
            return "end"
        else:
            logger.warning(f"Verificação para paciente {state.get('patient_id')} falhou ou requer replanejamento. Voltando para o planejamento.")
            # Prepara as instruções para o replanejamento
            new_replan_instructions = f"Correção necessária: {verification_data.get('notes', 'N/A')}"
            # O estado é um dicionário, então podemos modificar a lista diretamente se ela já existir.
            if "replan_instructions" in state:
                state["replan_instructions"].append(new_replan_instructions)
            else:
                state["replan_instructions"] = [new_replan_instructions]
            return "replan"

    async def run_single_patient_flow(self, patient_id: str, initial_data: str):
        """
        Executa o fluxo completo do grafo para um único paciente.
        """
        logger.info(f"Iniciando fluxo de trabalho terapêutico para o paciente: {patient_id}")
        
        # Configuração da thread de execução (sessão)
        config = {"configurable": {"thread_id": patient_id}}
        
        # Input inicial para o grafo
        flow_input = {
            "patient_id": patient_id,
            "patient_data": initial_data,
            "replan_instructions": [], # Inicializa a lista de instruções de replanejamento
        }
        
        # Itera sobre a execução do grafo, mostrando o resultado de cada passo
        final_state = None
        async for s in self.graph_app.astream(flow_input, config=config):
            final_state = s
            logger.info("--- Estado Atual do Fluxo ---")
            for key, value in s.items():
                logger.info(f"[{key}]: {value}")
            logger.info("----------------------------")
            
        logger.info(f"Fluxo de trabalho para o paciente {patient_id} concluído.")
        return final_state

# Instância única do grafo para ser usada pela API
therapeutic_workflow_graph = TherapeuticWorkflowGraph()
