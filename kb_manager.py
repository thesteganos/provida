# kb_manager.py
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Importa o nosso carregador de configuração
from config_loader import config

class KnowledgeBaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.graph = Neo4jGraph(
                url=os.getenv("NEO4J_URI"),
                username=os.getenv("NEO4J_USERNAME"),
                password=os.getenv("NEO4J_PASSWORD")
            )
            # Obtém o modelo de embedding a partir da configuração
            self.embeddings = config.get_embedding_model()
            self.retriever = self._init_rag_retriever()
            self.initialized = True
    
    # O resto do arquivo permanece o mesmo...
    def _init_rag_retriever(self):
        loader = TextLoader("./data/abeso_diretrizes_obesidade.txt")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        print(f"Indexando {len(docs)} chunks de documentos para RAG...")
        db = FAISS.from_documents(docs, self.embeddings)
        print("Indexação RAG completa.")
        return db.as_retriever()

    def add_patient_data(self, patient_id: str, data: dict):
        self.graph.query(
            "MERGE (p:Patient {id: $patient_id}) SET p += $props",
            params={"patient_id": patient_id, "props": data}
        )
        print(f"Dados para o paciente {patient_id} adicionados/atualizados no Neo4j.")

    def rag_query(self, query: str) -> str:
        docs = self.retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs])

kb_manager = KnowledgeBaseManager()
