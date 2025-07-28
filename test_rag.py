import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.app.rag import perform_rag_query, get_chroma_collection
from src.app.models.rag_models import RagResponse

# --- Fixtures para Mocks ---

@pytest.fixture
def mock_chroma_collection():
    mock_collection = MagicMock()
    # Configuração padrão para happy path
    mock_collection.query.return_value = {
        "documents": [["chunk1: Conteúdo do Artigo A.", "chunk2: Conteúdo do Artigo B."]],
        "metadatas": [[{"source": "ArtigoA.pdf"}, {"source": "ArtigoB.pdf"}]]
    }
    return mock_collection

@pytest.fixture
def mock_llm_provider():
    mock_provider = MagicMock()
    mock_model = AsyncMock()
    # Configuração padrão para happy path
    mock_model.generate_content_async.return_value.text = "Resumo gerado pelo LLM com base nos chunks."
    mock_provider.get_model.return_value = mock_model
    return mock_provider

# --- Testes para perform_rag_query ---

@pytest.mark.asyncio
async def test_perform_rag_query_happy_path(mock_chroma_collection, mock_llm_provider):
    with patch('src.app.rag.get_chroma_collection', return_value=mock_chroma_collection):
        with patch('src.app.rag.llm_provider', mock_llm_provider):
            query = "qual a dose de vitamina D?"
            response = await perform_rag_query(query)

            assert isinstance(response, RagResponse)
            assert "Resumo gerado pelo LLM com base nos chunks." in response.summary
            assert "ArtigoA.pdf" in response.sources
            assert "ArtigoB.pdf" in response.sources
            mock_chroma_collection.query.assert_called_once_with(query_texts=[query], n_results=5)
            mock_llm_provider.get_model.assert_called_once_with(mock_llm_provider.get_model.call_args[0][0]) # Verifica que get_model foi chamado
            mock_llm_provider.get_model().generate_content_async.assert_called_once()

@pytest.mark.asyncio
async def test_perform_rag_query_empty_query():
    with pytest.raises(ValueError, match="A consulta não pode ser vazia."):
        await perform_rag_query("")

@pytest.mark.asyncio
async def test_perform_rag_query_no_documents_found(mock_chroma_collection, mock_llm_provider):
    mock_chroma_collection.query.return_value = {
        "documents": [[]],
        "metadatas": [[]]
    }

    with patch('src.app.rag.get_chroma_collection', return_value=mock_chroma_collection):
        with patch('src.app.rag.llm_provider', mock_llm_provider):
            query = "consulta sem resultados"
            response = await perform_rag_query(query)

            assert isinstance(response, RagResponse)
            assert "Não foi encontrada informação relevante" in response.summary
            assert response.sources == []
            mock_chroma_collection.query.assert_called_once_with(query_texts=[query], n_results=5)
            mock_llm_provider.get_model().generate_content_async.assert_not_called() # LLM não deve ser chamado

@pytest.mark.asyncio
async def test_perform_rag_query_detail_levels(mock_chroma_collection, mock_llm_provider):
    with patch('src.app.rag.get_chroma_collection', return_value=mock_chroma_collection):
        with patch('src.app.rag.llm_provider', mock_llm_provider):
            # Teste para 'breve'
            query_breve = "resumo breve"
            await perform_rag_query(query_breve, detail_level="breve")
            prompt_breve = mock_llm_provider.get_model().generate_content_async.call_args[0][0]
            assert "1-2 frases" in prompt_breve

            # Teste para 'detalhado'
            mock_llm_provider.get_model().generate_content_async.reset_mock()
            query_detalhado = "resumo detalhado"
            await perform_rag_query(query_detalhado, detail_level="detalhado")
            prompt_detalhado = mock_llm_provider.get_model().generate_content_async.call_args[0][0]
            assert "6-8 frases" in prompt_detalhado

@pytest.mark.asyncio
async def test_perform_rag_query_chroma_connection_error(mock_llm_provider):
    with patch('src.app.rag.get_chroma_collection', side_effect=Exception("Erro de conexão ChromaDB")):
        with pytest.raises(Exception, match="Erro de conexão ChromaDB"):
            await perform_rag_query("teste erro conexao")

@pytest.mark.asyncio
async def test_perform_rag_query_llm_error(mock_chroma_collection, mock_llm_provider):
    mock_llm_provider.get_model().generate_content_async.side_effect = Exception("Erro na API do LLM")

    with patch('src.app.rag.get_chroma_collection', return_value=mock_chroma_collection):
        with patch('src.app.rag.llm_provider', mock_llm_provider):
            query = "teste erro llm"
            with pytest.raises(Exception, match="Erro na API do LLM"):
                await perform_rag_query(query)

@pytest.mark.asyncio
async def test_get_chroma_collection_cached():
    # Clear the cache before the test to ensure a fresh start
    get_chroma_collection.cache_clear()

    with patch('chromadb.HttpClient') as mock_http_client:
        mock_client_instance = MagicMock()
        mock_http_client.return_value = mock_client_instance
        mock_client_instance.get_or_create_collection.return_value = MagicMock()

        # Call twice to ensure caching
        collection1 = get_chroma_collection()
        collection2 = get_chroma_collection()

        # Assert that HttpClient is called only once, confirming caching
        mock_http_client.assert_called_once()
        assert collection1 is collection2

@pytest.mark.asyncio
async def test_get_chroma_collection_connection_error():
    with patch('chromadb.HttpClient', side_effect=Exception("Falha na conexão HTTP")):
        with pytest.raises(Exception, match="Falha na conexão HTTP"):
            # Clear cache before testing connection error
            get_chroma_collection.cache_clear()
            get_chroma_collection()

@pytest.mark.asyncio
async def test_perform_rag_query_sources_with_missing_metadata(mock_chroma_collection, mock_llm_provider):
    mock_chroma_collection.query.return_value = {
        "documents": [["chunk1", "chunk2"]],
        "metadatas": [[{"source": "ArtigoA.pdf"}, {}]] # Um metadata sem 'source'
    }

    with patch('src.app.rag.get_chroma_collection', return_value=mock_chroma_collection):
        with patch('src.app.rag.llm_provider', mock_llm_provider):
            query = "query com metadata faltando"
            response = await perform_rag_query(query)

            assert isinstance(response, RagResponse)
            assert "ArtigoA.pdf" in response.sources
            assert "Fonte desconhecida" in response.sources # Deve incluir a fonte desconhecida

@pytest.mark.asyncio
async def test_perform_rag_query_sources_with_empty_metadata(mock_chroma_collection, mock_llm_provider):
    mock_chroma_collection.query.return_value = {
        "documents": [["chunk1"]],
        "metadatas": [[None]] # Metadata é None
    }

    with patch('src.app.rag.get_chroma_collection', return_value=mock_chroma_collection):
        with patch('src.app.rag.llm_provider', mock_llm_provider):
            query = "query com metadata None"
            response = await perform_rag_query(query)

            assert isinstance(response, RagResponse)
            assert "Fonte desconhecida" in response.sources
            assert len(response.sources) == 1