from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from app.agents.planning_agent import PlanningAgent
from app.agents.research_agent import ResearchAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.synthesis_agent import SynthesisAgent

# 1. Define Graph State
class ResearchState(TypedDict):
    topic: str
    research_plan: Dict[str, Any]
    collected_data: List[Dict[str, Any]]
    analyzed_data: List[Dict[str, Any]]
    final_report: Dict[str, Any]

# 2. Define Nodes
def plan_research(state: ResearchState) -> ResearchState:
    planning_agent = PlanningAgent()
    research_plan = planning_agent.generate_research_plan(state["topic"])
    return {"research_plan": research_plan}

def execute_research(state: ResearchState) -> ResearchState:
    research_agent = ResearchAgent()
    collected_data = []
    # This is a simplified execution. In a real scenario, it would iterate through the plan.
    # For now, let's just do a single search based on the main topic.
    results = research_agent.search(state["topic"], search_type="auto")
    collected_data.append({"query": state["topic"], "results": results})
    return {"collected_data": collected_data}

def analyze_data(state: ResearchState) -> ResearchState:
    analysis_agent = AnalysisAgent()
    analyzed_data = []
    for item in state["collected_data"]:
        # Assuming 'results' contains text content to analyze
        if "results" in item and isinstance(item["results"], dict) and "text" in item["results"]:
            classification = analysis_agent.classify_evidence(item["results"]["text"])
            analyzed_data.append({"original_query": item["query"], "classification": classification})
        elif "results" in item and isinstance(item["results"], list):
            # Handle PubMed results (list of dicts)
            for result in item["results"]:
                if "abstract" in result:
                    classification = analysis_agent.classify_evidence(result["abstract"])
                    analyzed_data.append({"original_query": item["query"], "article_title": result.get("title"), "classification": classification})
    return {"analyzed_data": analyzed_data}

def synthesize_report(state: ResearchState) -> ResearchState:
    synthesis_agent = SynthesisAgent()
    # For simplicity, let's synthesize based on analyzed data
    # In a real scenario, this would be more sophisticated.
    text_to_summarize = ""
    sources = []
    source_id_counter = 1
    for item in state["analyzed_data"]:
        if "classification" in item and "justification" in item["classification"]:
            text_to_summarize += f"Evidence Level: {item['classification']['evidence_level']}. Justification: {item['classification']['justification']}.\n"
            sources.append({"id": str(source_id_counter), "content": item['classification']['justification']})
            source_id_counter += 1
        if "article_title" in item:
            text_to_summarize += f"Article: {item['article_title']}.\n"

    research_question = state["topic"] # Using topic as research question for now
    final_report = synthesis_agent.generate_summary_with_citations(text_to_summarize, research_question, sources)
    return {"final_report": final_report}

# 3. Build Graph
def build_research_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("plan", plan_research)
    workflow.add_node("execute", execute_research)
    workflow.add_node("analyze", analyze_data)
    workflow.add_node("synthesize", synthesize_report)

    workflow.set_entry_point("plan")

    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "analyze")
    workflow.add_edge("analyze", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()
