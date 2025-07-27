from rich.console import Console

def run_fast_query(query: str):
    """Executa o modo de consulta rápida."""
    console = Console()
    console.print(f"Executando Consulta Rápida para: '{query}'")
    from app.tools.web_search import search_web
    results = search_web(query)
    console.print(results)
