# kb_manager.py
import os
import shutil
import hashlib
import logging # Adicionado logging
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
# Tentar importar exceções específicas do Neo4j para captura mais granular
try:
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    # Fallback para uma exceção genérica se as específicas não estiverem disponíveis
    # (embora geralmente estejam com o driver neo4j instalado)
    ServiceUnavailable = Exception
    AuthError = Exception

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config_loader import config

class KnowledgeBaseManager:
    _instance = None

    def __init__(self):
        if not hasattr(self, 'initialized'):
            logging.info("Inicializando o Gerenciador da Base de Conhecimento (KnowledgeBaseManager)...")
            self.graph = None # Inicializa como None
            try:
                self.graph = Neo4jGraph(
                    url=os.getenv("NEO4J_URI"),
                    username=os.getenv("NEO4J_USERNAME"),
                    password=os.getenv("NEO4J_PASSWORD")
                )
                # Tenta uma query simples para verificar a conexão
                self.graph.query("RETURN 1")
                logging.info("Conexão com Neo4j estabelecida com sucesso.")
            except AuthError as e:
                logging.error(f"Erro de autenticação com Neo4j: {e}. Verifique suas credenciais NEO4J_USER/NEO4J_PASSWORD.")
                # A aplicação pode não funcionar corretamente sem o grafo.
                # Considerar levantar a exceção ou ter um modo de fallback mais robusto.
                # Por enquanto, self.graph permanecerá None.
            except ServiceUnavailable as e:
                logging.error(f"Serviço Neo4j indisponível em {os.getenv('NEO4J_URI')}: {e}. O grafo de conhecimento não estará funcional.")
                # self.graph permanecerá None. A aplicação pode continuar com funcionalidade limitada.
            except Exception as e:
                logging.error(f"Erro inesperado ao conectar com Neo4j: {e}", exc_info=True)
                # self.graph permanecerá None.

            self.embeddings = config.get_embedding_model()
            self.vectorstore_path = "./faiss_index"
            self.sources_dir = "./knowledge_sources"
            self.content_hash_log = os.path.join(self.sources_dir, "content_hashes.log")
            
            os.makedirs(self.sources_dir, exist_ok=True)
            self.content_hashes = self._get_processed_hashes()
            self.vectorstore = self._load_or_create_vectorstore()
            
            rag_cfg = config._config.get('rag_config', {})
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": rag_cfg.get('top_k_results', 3)}
            )
            self.initialized = True
            print("Gerenciador da Base de Conhecimento pronto.")

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
        return cls._instance

    def _get_processed_hashes(self) -> set:
        if not os.path.exists(self.content_hash_log):
            return set()
        with open(self.content_hash_log, 'r') as f:
            return set(line.strip() for line in f)

    def _log_content_hash(self, content_hash: str):
        with open(self.content_hash_log, 'a') as f:
            f.write(f"{content_hash}\n")
        self.content_hashes.add(content_hash)

    def _generate_content_hash(self, documents: list) -> str:
        full_text = "".join(doc.page_content for doc in documents).encode('utf-8')
        return hashlib.sha256(full_text).hexdigest()

    def _is_semantically_duplicate(self, documents: list, threshold=0.98) -> bool:
        if not documents or self.vectorstore.index.ntotal == 0:
            return False
        query_text = documents[0].page_content
        similar_docs_with_scores = self.vectorstore.similarity_search_with_score(query_text, k=1)
        if similar_docs_with_scores:
            score = similar_docs_with_scores[0][1]
            similarity = 1 - (score**2 / 2)
            if similarity > threshold:
                print(f"Potencial duplicado semântico encontrado com similaridade de {similarity:.4f}.")
                return True
        return False

    def _load_or_create_vectorstore(self) -> FAISS:
        if os.path.exists(self.vectorstore_path):
            print(f"Carregando VectorStore existente de '{self.vectorstore_path}'...")
            return FAISS.load_local(self.vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            print("Nenhum VectorStore encontrado. Criando um novo do zero...")
            return self._create_vectorstore_from_scratch()

    def _create_vectorstore_from_scratch(self) -> FAISS:
        print(f"Lendo documentos de '{self.sources_dir}'...")
        loader = DirectoryLoader(
            self.sources_dir, glob="**/*[.pdf,.txt]",
            loader_cls=lambda p: PyPDFLoader(p) if p.endswith('.pdf') else TextLoader(p),
            show_progress=True, use_multithreading=True
        )
        documents = loader.load()
        if not documents:
            print("AVISO: Nenhum documento encontrado para indexar.")
            db = FAISS.from_texts(["placeholder"], self.embeddings)
            db.save_local(self.vectorstore_path)
            return db

        rag_cfg = config._config.get('rag_config', {})
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_cfg.get('chunk_size', 1000), chunk_overlap=rag_cfg.get('chunk_overlap', 200)
        )
        docs = text_splitter.split_documents(documents)
        
        print(f"Indexando {len(docs)} chunks...")
        db = FAISS.from_documents(docs, self.embeddings)
        db.save_local(self.vectorstore_path)
        
        open(self.content_hash_log, 'w').close()
        source_docs = {}
        for doc in documents:
            source_path = doc.metadata['source']
            if source_path not in source_docs: source_docs[source_path] = []
            source_docs[source_path].append(doc)
            
        for source, doc_list in source_docs.items():
            self._log_content_hash(self._generate_content_hash(doc_list))
        
        return db

    def ingest_new_document(self, file_path: str) -> str:
        filename = os.path.basename(file_path)
        try:
            loader = PyPDFLoader(file_path) if filename.endswith('.pdf') else TextLoader(file_path)
            documents = loader.load()
        except Exception as e:
            return f"Erro ao ler o documento '{filename}': {e}"

        if not documents: return f"Documento '{filename}' está vazio."

        content_hash = self._generate_content_hash(documents)
        if content_hash in self.content_hashes:
            return f"DEDUPLICAÇÃO POR HASH: O conteúdo de '{filename}' já existe."

        if self._is_semantically_duplicate(documents):
            return f"DEDUPLICAÇÃO SEMÂNTICA: O conteúdo de '{filename}' é muito similar a um já existente."

        rag_cfg = config._config.get('rag_config', {})
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_cfg.get('chunk_size', 1000), chunk_overlap=rag_cfg.get('chunk_overlap', 200)
        )
        docs = text_splitter.split_documents(documents)
        
        self.vectorstore.add_documents(docs)
        self.vectorstore.save_local(self.vectorstore_path)
        self._log_content_hash(content_hash)
        return f"Documento '{filename}' ingerido e indexado com sucesso."

    def add_patient_data(self, patient_id: str, data: dict):
        if self.graph:
            try:
                self.graph.query("MERGE (p:Patient {id: $patient_id}) SET p += $props", params={"patient_id": patient_id, "props": data})
                logging.info(f"Dados para o paciente {patient_id} adicionados/atualizados no Neo4j.")
            except Exception as e:
                logging.error(f"Falha ao adicionar dados do paciente {patient_id} ao Neo4j: {e}", exc_info=True)
        else:
            logging.warning(f"Neo4j indisponível. Não foi possível adicionar/atualizar dados para o paciente {patient_id}.")

    def rag_query(self, query: str) -> str:
        # Esta função depende do self.retriever, que é baseado no FAISS e não diretamente no Neo4j.
        # No entanto, se o Neo4j fosse usado como parte do RAG (ex: Knowledge Graph RAG),
        # seria necessário verificar self.graph aqui também.
        # Por ora, o RAG atual parece independente do Neo4j após a inicialização do FAISS.
        docs = self.retriever.invoke(query)
        if not docs: return "Nenhuma informação relevante encontrada na base de conhecimento."
        return "\n\n---\n\n".join([f"Fonte: {os.path.basename(doc.metadata.get('source', 'N/A'))}\n\n{doc.page_content}" for doc in docs])

kb_manager = KnowledgeBaseManager()
