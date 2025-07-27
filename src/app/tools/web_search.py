from src.app.tools.brave_search import BraveSearch
from src.app.tools.pubmed_search import PubMedSearch
from src.app.config.settings import settings

def search_web(query, search_type="general", count=10):
    if search_type == "academic":
        pubmed_search = PubMedSearch()
        return pubmed_search.search(query, count=count)
    elif search_type == "general":
        brave_search = BraveSearch()
        return brave_search.search(query, count=count)
    elif search_type == "auto":
        # Placeholder logic for auto detection
        if "academic" in query.lower():
            pubmed_search = PubMedSearch()
            return pubmed_search.search(query, count=count)
        else:
            brave_search = BraveSearch()
            return brave_search.search(query, count=count)
    else:
        raise ValueError(f"Invalid search type: {search_type}")
