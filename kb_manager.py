# kb_manager.py
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class KnowledgeBaseManager:
    """Gerencia a interação com Neo4j e o VectorStore para RAG."""
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
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            self.retriever = self._init_rag_retriever()
            self.initialized = True

    def _init_rag_retriever(self):
        """Carrega, divide e indexa documentos para o sistema RAG."""
        # Para este exemplo, carregamos um arquivo de texto simples.
        # Poderia ser estendido para PDFs, etc.
        loader = TextLoader("./data/abeso_diretrizes_obesidade.txt")
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        
        print(f"Indexando {len(docs)} chunks de documentos para RAG.")
        db = FAISS.from_documents(docs, self.embeddings)
        return db.as_retriever()

    def add_patient_data(self, patient_id: str, data: dict):
        """Cria ou atualiza o KG do Paciente no Neo4j."""
        # Cria um nó para o paciente se não existir
        self.graph.query(
            "MERGE (p:Patient {id: $patient_id}) SET p += $props",
            params={"patient_id": patient_id, "props": data}
        )
        print(f"Dados para o paciente {patient_id} adicionados/atualizados no Neo4j.")

    def query_patient_kg(self, patient_id: str, query: str) -> list:
        """Executa uma query no KG do Paciente."""
        # Esta é uma implementação simplificada. Uma real teria um parser de NL para Cypher.
        # Aqui, apenas retornamos os dados do paciente.
        result = self.graph.query("MATCH (p:Patient {id: $patient_id}) RETURN p", params={'patient_id': patient_id})
        return result
        
    def rag_query(self, query: str) -> str:
        """Busca informações no banco de dados vetorial (RAG)."""
        docs = self.retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs])

# Singleton para garantir uma única conexão
kb_manager = KnowledgeBaseManager()
