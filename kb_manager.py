# kb_manager.py
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Importa o wrapper para embeddings locais da Hugging Face
from langchain_community.embeddings import HuggingFaceEmbeddings

class KnowledgeBaseManager:
    """Gerencia a interação com Neo4j e o VectorStore para RAG usando embeddings locais."""
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
            
            # --- MUDANÇA PRINCIPAL: USA EMBEDDINGS LOCAIS ---
            # Escolhe um modelo leve e eficiente que será baixado e executado localmente.
            # 'all-MiniLM-L6-v2' é um ótimo ponto de partida.
            print("Inicializando modelo de embedding local (pode levar um tempo na primeira vez)...")
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            model_kwargs = {'device': 'cpu'} # Use 'cuda' se tiver GPU
            encode_kwargs = {'normalize_embeddings': False}
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            print("Modelo de embedding local carregado.")
            
            self.retriever = self._init_rag_retriever()
            self.initialized = True

    def _init_rag_retriever(self):
        """Carrega, divide e indexa documentos para o sistema RAG."""
        loader = TextLoader("./data/abeso_diretrizes_obesidade.txt")
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        
        print(f"Indexando {len(docs)} chunks de documentos para RAG com embeddings locais...")
        db = FAISS.from_documents(docs, self.embeddings)
        print("Indexação RAG completa.")
        return db.as_retriever()

    def add_patient_data(self, patient_id: str, data: dict):
        """Cria ou atualiza o KG do Paciente no Neo4j."""
        self.graph.query(
            "MERGE (p:Patient {id: $patient_id}) SET p += $props",
            params={"patient_id": patient_id, "props": data}
        )
        print(f"Dados para o paciente {patient_id} adicionados/atualizados no Neo4j.")

    def rag_query(self, query: str) -> str:
        """Busca informações no banco de dados vetorial (RAG)."""
        docs = self.retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs])

# Singleton para garantir uma única conexão
kb_manager = KnowledgeBaseManager()
