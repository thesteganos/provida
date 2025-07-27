from app.tools.web_search import search_web
from app.core.llm_provider import llm_provider
from app.config.settings import settings

class ResearchAgent:
    def __init__(self):
        # The LLM model will be used for analysis/synthesis, not directly for search execution here.
        # We can keep it for future use or remove if not immediately needed for search.
        # For now, let's keep it as a placeholder for future LLM-driven search query generation/refinement.
        self.llm_model = llm_provider.get_model(settings["models"]["rag_query_agent"])

    def search(self, query: str, search_type: str = "auto"):
        """Performs a web search using the integrated search tools."""
        # In a later phase, the LLM might generate/refine the query before calling search_web
        # For now, directly call the search_web tool.
        return search_web(query, search_type)
