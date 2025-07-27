import chromadb
from chromadb.utils import embedding_functions
from app.config.settings import settings
from typing import List, Dict, Any

def get_vector_db_client():
    """Initializes and returns a ChromaDB client."""
    db_path = settings["services"]["vector_db"]["path"]
    client = chromadb.PersistentClient(path=db_path)
    return client

def get_embedding_function():
    """Returns a default embedding function (e.g., SentenceTransformers)."""
    # For a real application, you might want to use a more robust embedding function
    # like one provided by Google's models or OpenAI.
    # This is a placeholder for initial setup.
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def add_documents(collection_name: str, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
    """Adds documents to a specified ChromaDB collection.

    Args:
        collection_name (str): The name of the collection.
        documents (List[str]): A list of document texts.
        metadatas (List[Dict[str, Any]]): A list of metadata dictionaries, one for each document.
        ids (List[str]): A list of unique IDs for each document.
    """
    client = get_vector_db_client()
    embedding_function = get_embedding_function()
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Added {len(documents)} documents to collection '{collection_name}'.")

def search_documents(collection_name: str, query_texts: List[str], n_results: int = 5) -> List[Dict[str, Any]]:
    """Searches for similar documents in a specified ChromaDB collection.

    Args:
        collection_name (str): The name of the collection.
        query_texts (List[str]): A list of query texts.
        n_results (int): The number of results to return for each query.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing search results.
    """
    client = get_vector_db_client()
    embedding_function = get_embedding_function()
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)
    results = collection.query(query_texts=query_texts, n_results=n_results)
    return results