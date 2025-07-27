import asyncio
import logging
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.analysis_agent import AnalysisAgent
from app.agents.knowledge_graph_agent import KnowledgeGraphAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.services.fact_checking_service import verify_text_against_kg

logger = logging.getLogger(__name__)


class ResearchState(TypedDict):
    """
    Representa o estado do grafo de pesquisa.
    """

    topic: str
    research_plan: Dict[str, Any]
    # Mock de dados coletados para demonstração
    collected_data: List[Dict[str, Any]]
    analyzed_data: List[Dict[str, Any]]
    final_report: Dict[str, Any]
    verification_report: Dict[str, Any]


# --- Nós do Grafo ---


def plan_node(state: ResearchState) -> Dict[str, Any]:
    """
    Nó responsável por gerar o plano de pesquisa.
    (Implementação mockada para este exemplo)
    """
    logger.info(f"Gerando plano de pesquisa para o tópico: {state['topic']}")
    # Em uma implementação real, chamaria o PlanningAgent
    # planning_agent = PlanningAgent()
    # plan = planning_agent.generate_research_plan(state['topic'])
    plan = {"plan": [{"step": "Analisar dados iniciais"}]}
    # Mock de dados coletados para o próximo passo
    collected_data = [
        {
            "source_identifier": "https://example.com/artigo1",
            "content": "A vitamina D é crucial para a absorção de cálcio.",
        }
    ]
    return {"research_plan": plan, "collected_data": collected_data}


async def analysis_node(state: ResearchState) -> Dict[str, Any]:
    """
    Nó que executa a análise dos dados coletados.
    """
    logger.info("Analisando dados coletados...")
    analysis_agent = AnalysisAgent()
    tasks = [
        analysis_agent.classify_evidence(item["content"])
        for item in state["collected_data"]
    ]
    analysis_results = await asyncio.gather(*tasks)

    # Combina o resultado da análise com o identificador da fonte
    analyzed_data = [
        {"source_identifier": item["source_identifier"], "analysis": result}
        for item, result in zip(state["collected_data"], analysis_results)
    ]
    return {"analyzed_data": analyzed_data}


async def knowledge_graph_node(state: ResearchState) -> None:
    """
    Nó que atualiza o grafo de conhecimento com os resultados da análise.
    """
    logger.info("Atualizando o grafo de conhecimento...")
    kg_agent = KnowledgeGraphAgent()
    tasks = [
        kg_agent.update_graph_with_analysis(
            source_identifier=item["source_identifier"],
            analysis_data=item["analysis"],
            research_topic=state["topic"],
        )
        for item in state["analyzed_data"]
    ]
    await asyncio.gather(*tasks)
    return {}  # Este nó não modifica o estado, apenas tem um efeito colateral


async def synthesis_node(state: ResearchState) -> Dict[str, Any]:
    """
    Nó que sintetiza os dados analisados em um relatório final.
    """
    logger.info("Sintetizando o relatório final...")
    synthesis_agent = SynthesisAgent()

    # Combina o conteúdo analisado em um único texto para síntese
    # e prepara as fontes para citação
    full_text_content = "\n\n".join(
        item["analysis"].get("summary", "") for item in state["analyzed_data"]
    )
    sources_for_citation = [
        {"id": item["source_identifier"], "content": item["analysis"].get("summary", "")}
        for item in state["analyzed_data"]
    ]

    report = await synthesis_agent.generate_summary_with_citations(
        text=full_text_content,
        research_question=state["topic"],
        sources=sources_for_citation,
    )
    return {"final_report": report}


async def fact_check_node(state: ResearchState) -> Dict[str, Any]:
    """
    Nó que verifica as alegações do relatório final contra o grafo de conhecimento.
    """
    logger.info("Verificando fatos do relatório final...")
    summary_text = state["final_report"].get("summary")

    if not summary_text:
        logger.warning("Nenhum resumo para verificar. Pulando a verificação de fatos.")
        return {"verification_report": {"hallucination_detected": False, "message": "No summary to check."}}

    report = await verify_text_against_kg(summary_text)
    return {"verification_report": report}


def build_research_graph():
    """Constrói e compila o grafo de pesquisa do LangGraph."""
    workflow = StateGraph(ResearchState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("analyze", analysis_node)
    workflow.add_node("update_kg", knowledge_graph_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("fact_check", fact_check_node)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "analyze")
    workflow.add_edge("analyze", "update_kg")
    workflow.add_edge("update_kg", "synthesis")
    workflow.add_edge("synthesis", "fact_check")
    workflow.add_edge("fact_check", END)

    return workflow.compile()