import asyncio
import logging
from functools import lru_cache
from typing import Optional

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
    except chromadb.errors.ChromaError as e:
        logger.critical(f"Falha ao conectar ou configurar a coleção do ChromaDB: {e}", exc_info=True)
        raise ConnectionError(f"Não foi possível conectar ao ChromaDB: {e}")
    except Exception as e:
        logger.critical(f"Um erro inesperado ocorreu ao tentar obter a coleção do ChromaDB: {e}", exc_info=True)
        raise


async def perform_rag_query(query: str, detail_level: str = "padrao") -> RagResponse:
    """
    Executa uma consulta RAG completa: busca no ChromaDB e síntese com LLM.

    Args:
        query (str): A pergunta do usuário.
        detail_level (str): Nível de detalhe para o resumo (breve, padrao, detalhado).

    Returns:
        RagResponse: Um objeto contendo o resumo e as fontes da resposta.
    """
    if not query:
        raise ValueError("A consulta não pode ser vazia.")

    collection = get_chroma_collection()

    # 1. Buscar chunks de documentos relevantes no ChromaDB
    results = collection.query(query_texts=[query], n_results=settings.rag.n_results)

    documents = []
    metadatas = []

    if results and "documents" in results and len(results["documents"]) > 0:
        documents = results["documents"][0]
    if results and "metadatas" in results and len(results["metadatas"]) > 0:
        metadatas = results["metadatas"][0]

    if not documents:
        return RagResponse(
            summary="Não foi encontrada informação relevante na base de conhecimento para responder à sua pergunta.",
            sources=[],
        )

    context = "\n\n".join(documents)
    sources = list(set(meta.get("source", "Fonte desconhecida") for meta in metadatas if meta))

    # 2. Preparar o prompt para o LLM com base no nível de detalhe
    from app.prompts.llm_prompts import RAG_PROMPT_TEMPLATE, RAG_INSTRUCTIONS

    instruction = RAG_INSTRUCTIONS.get(detail_level, RAG_INSTRUCTIONS["padrao"])

    prompt = RAG_PROMPT_TEMPLATE.format(
        instruction=instruction,
        query=query,
        context=context
    )

    # 3. Chamar o LLM para gerar a síntese
    try:
        model = llm_provider.get_model(settings.models.rag_agent)
        response = await model.generate_content_async(prompt)
        return RagResponse(summary=response.text, sources=sources)
    except Exception as e:
        logger.error(f"Erro ao gerar a síntese com o LLM para a consulta '{query}': {e}", exc_info=True)
        # Retorna uma resposta de erro ou levanta uma exceção personalizada
        raise RuntimeError(f"Falha ao gerar resposta de RAG: {e}")
