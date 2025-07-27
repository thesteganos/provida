import asyncio
import logging
from functools import lru_cache

import chromadb
from chromadb.types import Collection

from app.config.settings import settings
from app.models.rag_models import RagResponse
from app.core.llm_provider import llm_provider

logger = logging.getLogger(__name__)


@lru_cache
def get_chroma_collection() -> Collection:
    """
    Cria e retorna um cliente ChromaDB conectado à coleção especificada.

    A instância do cliente e da coleção são cacheadas para reutilização,
    evitando múltiplas conexões. As configurações são lidas do objeto
    de settings global.

    Returns:
        Collection: A instância da coleção do ChromaDB.
    """
    try:
        client = chromadb.HttpClient(
            host=settings.database.chroma.host,
            port=settings.database.chroma.port,
        )
        collection = client.get_or_create_collection(
            name=settings.database.chroma.collection
        )
        logger.info(f"Conectado com sucesso à coleção '{settings.database.chroma.collection}' do ChromaDB.")
        return collection
    except Exception as e:
        logger.critical(f"Falha ao conectar ao ChromaDB: {e}", exc_info=True)
        raise


async def perform_rag_query(query: str) -> RagResponse:
    """
    Executa uma consulta RAG completa: busca no ChromaDB e síntese com LLM.

    Args:
        query (str): A pergunta do usuário.

    Returns:
        RagResponse: Um objeto contendo o resumo e as fontes da resposta.
    """
    if not query:
        raise ValueError("A consulta não pode ser vazia.")

    collection = get_chroma_collection()

    # 1. Buscar chunks de documentos relevantes no ChromaDB
    results = collection.query(query_texts=[query], n_results=5)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return RagResponse(
            summary="Não foi encontrada informação relevante na base de conhecimento para responder à sua pergunta.",
            sources=[],
        )

    context = "\n\n".join(documents)
    sources = list(set(meta.get("source", "Fonte desconhecida") for meta in metadatas if meta))

    # 2. Preparar o prompt para o LLM
    prompt = f"""Com base nos seguintes trechos de documentos, responda à pergunta do usuário de forma concisa e direta.
Pergunta: {query}

Documentos:
{context}

Resposta:"""

    # 3. Chamar o LLM para gerar a síntese
    model = llm_provider.get_model(settings.models.rag_agent)
    response = await model.generate_content_async(prompt)

    return RagResponse(summary=response.text, sources=sources)