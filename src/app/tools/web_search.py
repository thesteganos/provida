"""Utilidades de busca na web."""

from src.app.tools.brave_search import BraveSearch
from src.app.tools.pubmed_search import PubMedSearch
from src.app.config.settings import settings

FORBIDDEN_TOPICS = ["programming", "machine learning"]
ALLOWED_TOPICS = ["bariatric", "bariátrica", "obesity", "obesidade"]

from typing import List, Optional


async def search_web(
    query: str,
    search_type: str = "general",
    count: int = 10,
    allowed_topics: Optional[List[str]] = None,
):
    """Realiza buscas na web priorizando bariátrica e obesidade.

    Se a consulta contiver termos sobre programação ou *machine learning*
    sem relação com cirurgia bariátrica ou tratamento da obesidade, o
    texto é substituído por "cirurgia bariátrica e tratamento da obesidade".

    Parâmetros
    ----------
    query: str
        Texto de busca original.
    search_type: str
        "general", "academic" ou "auto".
    count: int
        Quantidade de resultados a retornar.
    allowed_topics: Optional[List[str]]
        Lista de temas extras permitidos pelo usuário.
    """

    lowered = query.lower()
    topics = ALLOWED_TOPICS if allowed_topics is None else ALLOWED_TOPICS + allowed_topics
    if any(t in lowered for t in FORBIDDEN_TOPICS) and not any(
        a in lowered for a in topics
    ):
        query = "cirurgia bariátrica e tratamento da obesidade"

    if search_type == "academic":
        pubmed_search = PubMedSearch()
        return await pubmed_search.search(query, count=count)
    if search_type == "general":
        brave_search = BraveSearch()
        return await brave_search.search(query, count=count)
    if search_type == "auto":
        if "academic" in query.lower():
            pubmed_search = PubMedSearch()
            return await pubmed_search.search(query, count=count)
        brave_search = BraveSearch()
        return await brave_search.search(query, count=count)
    raise ValueError(f"Invalid search type: {search_type}")
