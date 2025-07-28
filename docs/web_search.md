# Web Search Module

The `web_search` module provides asynchronous helpers for querying the web. Two search backends are available:
Brave Search for general content and PubMed for academic references. The helper can also auto-detect which backend to use based on the query. Consultas sobre "programming" ou "machine learning" que não mencionem bariátrica ou obesidade são automaticamente substituídas por "cirurgia bariátrica e tratamento da obesidade", a menos que esses termos sejam incluídos em `allowed_topics`.

## `search_web(query, search_type="general", count=10, allowed_topics=None)`

- **Parameters**
  - `query` (`str`): text to search.
  - `search_type` (`str`): `general`, `academic`, or `auto` (default `general`).
  - `count` (`int`): number of results to return.
  - `allowed_topics` (`list[str] | None`): extra topics that bypass the bariatric filter.
- **Returns**: list of dictionaries with `title` and `url` keys.
- **Raises**: `ValueError` for unknown search types.

## Environment Variables

- `BRAVE_API_KEY` – required for Brave Search queries.
- `ENTREZ_EMAIL` and `ENTREZ_API_KEY` – required for PubMed queries.

Without these variables set, requests to the respective service will fail.

## Auto-Detection

When `search_type="auto"` the query is inspected for academic terms. Queries containing words such as
"study", "trial" or "pubmed" are routed to PubMed; otherwise Brave Search is used.

## Usage Examples

```python
from src.app.tools.web_search import search_web

results = await search_web("técnicas de cirurgia bariátrica", search_type="general", count=5)
for item in results:
    print(item["title"], item["url"])
```

```python
results = await search_web("tratamento da obesidade", search_type="academic", count=5)
```

```python
results = await search_web("últimos estudos sobre cirurgia bariátrica", search_type="auto", count=5)
```

```python
# Permite consulta sobre programação sem substituição
results = await search_web(
    "Python programming",
    search_type="general",
    allowed_topics=["programming"]
)
```
