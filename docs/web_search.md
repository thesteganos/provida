# Web Search Module

The `web_search` module provides functionality to search the web for information using different search types, such as general web search and academic search. It also includes an auto-detection feature to determine the appropriate search type based on the query.

## Functions

### `search_web(query, search_type="general", count=10)`

Searches the web for the given query using the specified search type.

- **Parameters:**
  - `query` (str): The search query.
  - `search_type` (str): The type of search to perform. Can be "general", "academic", or "auto". Defaults to "general".
  - `count` (int): The number of search results to return. Defaults to 10.
  
- **Returns:**
  - A list of dictionaries, each containing the title and URL of a search result.

- **Raises:**
  - `ValueError`: If an invalid search type is provided.

## Usage Examples

### General Web Search

```python
from src.app.tools.web_search import search_web

results = search_web("Python programming", search_type="general", count=5)
for result in results:
    print(result['title'], result['url'])
```

### Academic Search

```python
from src.app.tools.web_search import search_web

results = search_web("Machine learning", search_type="academic", count=5)
for result in results:
    print(result['title'], result['url'])
```

### Auto-Detection

```python
from src.app.tools.web_search import search_web

results = search_web("research on climate change", search_type="auto", count=5)
for result in results:
    print(result['title'], result['url'])