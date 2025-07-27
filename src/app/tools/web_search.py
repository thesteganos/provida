from app.tools.brave_search import BraveSearch
from app.tools.pubmed_search import PubMedSearch
from typing import Union, List, Dict, Any

def search_web(query: str, search_type: str = "auto") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Performs a web search using Brave Search or PubMed Search based on query type.

    Args:
        query (str): The search query.
        search_type (str): 'auto', 'general', or 'academic'. Defaults to 'auto'.

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: Search results from the chosen API.
    """
    brave_search = BraveSearch()
    pubmed_search = PubMedSearch()

    academic_keywords = ["bariatric", "surgery", "medical", "clinical trial", "study", "pubmed", "article", "research", "journal", "diagnosis", "treatment", "patient", "complication", "outcome", "meta-analysis", "randomized controlled trial"]

    if search_type == "academic":
        print(f"Performing academic search for: {query}")
        return pubmed_search.search(query)
    elif search_type == "general":
        print(f"Performing general web search for: {query}")
        return brave_search.search(query)
    elif search_type == "auto":
        if any(keyword in query.lower() for keyword in academic_keywords):
            print(f"Auto-detect: Performing academic search for: {query}")
            return pubmed_search.search(query)
        else:
            print(f"Auto-detect: Performing general web search for: {query}")
            return brave_search.search(query)
    else:
        raise ValueError("Invalid search_type. Must be 'auto', 'general', or 'academic'.")
