# kb_manager.py
"""
Este módulo, KnowledgeBaseManager, é o componente central para o gerenciamento
da base de conhecimento do sistema PROVIDA. Ele encapsula toda a lógica para
interagir com o grafo de conhecimento (Neo4j) e a base de dados vetorial
para busca de similaridade (FAISS).

Principais responsabilidades:
- Conectar-se e fornecer acesso à instância do banco de dados Neo4j.
- Inicializar e gerenciar o modelo de embeddings (ex: Google Generative AI).
- Carregar, processar e ingerir documentos (PDFs, texto) na base de conhecimento.
- A ingestão envolve dividir documentos em pedaços (chunks), gerar embeddings
  para esses chunks e armazená-los em um índice FAISS.
- Garantir a persistência do índice FAISS e dos metadados associados.
- Fornecer uma interface de consulta unificada (RAG - Retrieval-Augmented
  Generation) que busca documentos relevantes em FAISS com base em uma
  pergunta do usuário.
- Implementar verificação de duplicidade semântica para evitar a ingestão de
  documentos com conteúdo muito similar a algo que já existe na base.
"""
import logging
import os
import hashlib
from typing import List, Optional, Dict, Any, Tuple

from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader
from langchain_community.vectorstores import FAISS
from langchain_community.graphs import Neo4jGraph
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np

# Módulos locais
from config_loader import config

logger = logging.getLogger(__name__)

class KnowledgeBaseManager:
    """
    Gerencia a base de conhecimento, incluindo o grafo Neo4j e o RAG com FAISS.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Evita a reinicialização se a instância já existir
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        logger.info("Inicializando KnowledgeBaseManager...")

        # Carrega configurações do arquivo YAML
        # MODIFICADO: Acessando a configuração através do dicionário _config.
        self.rag_config = config._config.get('rag', {})
        self.model_config = config._config.get('models', {}).get('embedding', {})
        self.neo4j_config = config._config.get('neo4j', {})

        # Inicializa o cliente Neo4j
        try:
            self.graph = Neo4jGraph(
                url=self.neo4j_config.get("uri"),
                username=self.neo4j_config.get("user"),
                password=self.neo4j_config.get("password")
            )
            logger.info("Conexão com Neo4j estabelecida através do LangChain.")
        except Exception as e:
            logger.critical(f"Falha ao conectar com o Neo4j: {e}", exc_info=True)
            raise RuntimeError(f"Não foi possível conectar ao Neo4j: {e}") from e

        # Inicializa o modelo de embedding
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.model_config.get("name", "models/embedding-001"),
                google_api_key=self.model_config.get("api_key")
            )
            logger.info(f"Modelo de embedding '{self.model_config.get('name')}' carregado.")
        except Exception as e:
            logger.critical(f"Falha ao carregar o modelo de embedding: {e}", exc_info=True)
            raise RuntimeError(f"Não foi possível inicializar o modelo de embedding: {e}") from e

        # Configura o TextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.rag_config.get('chunk_size', 1000),
            chunk_overlap=self.rag_config.get('chunk_overlap', 200)
        )

        # Caminho para o armazenamento persistente do FAISS
        self.faiss_persist_path = self.rag_config.get('faiss_persist_path', "faiss_index")
        self.vector_store: Optional[FAISS] = self._load_vector_store()

        self._initialized = True
        logger.info("KnowledgeBaseManager inicializado com sucesso.")


    def _load_vector_store(self) -> Optional[FAISS]:
        """Carrega o vector store FAISS do disco, se existir."""
        if os.path.exists(self.faiss_persist_path) and os.path.exists(os.path.join(self.faiss_persist_path, "index.faiss")):
            try:
                logger.info(f"Carregando vector store FAISS de '{self.faiss_persist_path}'...")
                # FAISS.load_local requer que allow_dangerous_deserialization seja definido
                return FAISS.load_local(
                    self.faiss_persist_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True # Necessário para carregar o index.pkl
                )
            except Exception as e:
                logger.error(f"Erro ao carregar o vector store FAISS: {e}. Um novo será criado se necessário.", exc_info=True)
                return None
        else:
            logger.info("Nenhum vector store FAISS encontrado no disco. Será criado um novo na primeira ingestão.")
            return None

    def _get_file_hash(self, file_path: str) -> str:
        """Calcula o hash SHA256 de um arquivo para verificação de duplicidade."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_document_node(self, file_path: str, file_hash: str, status: str, metadata: Optional[Dict] = None):
        """Cria um nó de Documento no Neo4j para rastreamento."""
        query = """
        MERGE (d:Document {hash: $hash})
        ON CREATE SET d.filePath = $filePath, d.status = $status, d.createdAt = timestamp()
        ON MATCH SET d.status = $status, d.updatedAt = timestamp()
        """
        params = {
            "hash": file_hash,
            "filePath": file_path,
            "status": status,
        }
        if metadata:
            for key, value in metadata.items():
                query += f" SET d.{key} = ${key}"
                params[key] = value
        
        self.graph.query(query, params)
        logger.info(f"Nó de Documento criado/atualizado para hash: {file_hash[:8]}")

    def add_patient_data(self, patient_id: str, data: Dict[str, Any]):
        """Adiciona ou atualiza dados de um paciente no grafo Neo4j."""
        query = """
        MERGE (p:Patient {id: $id})
        SET p += $props, p.updatedAt = timestamp()
        """
        props = data.copy()
        params = {
            "id": patient_id,
            "props": props
        }
        self.graph.query(query, params)
        logger.info(f"Dados do paciente {patient_id} adicionados/atualizados no grafo.")


    def ingest_new_document(self, file_path: str) -> str:
        """
        Processa e ingere um novo documento (PDF, etc.) na base de conhecimento.
        Verifica se o documento já foi processado antes de ingerir.
        """
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado para ingestão: {file_path}")
            return f"Erro: Arquivo não encontrado em '{file_path}'"

        file_hash = self._get_file_hash(file_path)

        # Consulta o Neo4j para ver se este hash de arquivo já existe
        if self.graph.query("MATCH (d:Document {hash: $hash}) RETURN d", {"hash": file_hash}):
            logger.warning(f"Documento '{os.path.basename(file_path)}' com hash {file_hash} já existe no grafo. Ingestão pulada.")
            return f"Documento já existe (hash: {file_hash[:8]})"

        logger.info(f"Iniciando ingestão do novo documento: {file_path}")
        
        try:
            # Seleciona o loader apropriado com base na extensão do arquivo
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            else:
                # UnstructuredFileLoader pode lidar com .txt, .md, etc.
                loader = UnstructuredFileLoader(file_path)
            
            documents = loader.load()

            # Extrai o texto para verificação de duplicidade semântica
            full_text = " ".join([doc.page_content for doc in documents])
            if not full_text.strip():
                logger.warning(f"O documento '{file_path}' está vazio ou não contém texto extraível.")
                return "Documento vazio ou sem texto"

            # Verificação de duplicidade semântica antes de processar
            if self.is_semantically_duplicate(full_text):
                 logger.warning(f"Documento '{file_path}' é semanticamente similar a um existente. Ingestão pulada.")
                 # Ainda assim, cria o nó do documento para rastrear que ele foi visto
                 self.create_document_node(
                    file_path=file_path,
                    file_hash=file_hash,
                    status="skipped_semantic_duplicate"
                 )
                 return "Duplicidade semântica detectada"


            # Divide os documentos em chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Documento dividido em {len(chunks)} chunks.")

            # Adiciona os chunks ao vector store
            if self.vector_store is None:
                # Cria um novo vector store se for o primeiro documento
                logger.info("Criando novo vector store FAISS...")
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                # Adiciona ao vector store existente
                logger.info("Adicionando chunks ao vector store FAISS existente...")
                self.vector_store.add_documents(chunks)

            # Salva o índice FAISS e os metadados no disco
            self.vector_store.save_local(self.faiss_persist_path)
            logger.info(f"Vector store FAISS salvo em '{self.faiss_persist_path}'.")

            # Cria um nó no Neo4j para rastrear o documento processado
            self.create_document_node(
                file_path=file_path,
                file_hash=file_hash,
                status="ingested_successfully",
                metadata={"chunks": len(chunks), "source": os.path.basename(file_path)}
            )
            return "Ingestão realizada com sucesso"

        except Exception as e:
            logger.error(f"Falha ao ingerir o documento '{file_path}': {e}", exc_info=True)
            return f"Erro na ingestão: {e}"

    def is_semantically_duplicate(self, query_text: str, threshold: Optional[float] = None) -> bool:
        """
        Verifica se um texto é semanticamente duplicado em relação ao conteúdo existente.
        Retorna True se a similaridade com o documento mais próximo estiver acima do limiar.
        """
        if self.vector_store is None:
            return False # Não há nada para comparar

        if threshold is None:
            threshold = self.rag_config.get('semantic_similarity_threshold', 0.95)

        try:
            results_with_scores: List[Tuple[Any, float]] = self.vector_store.similarity_search_with_score(
                query_text, k=1
            )
            
            if not results_with_scores:
                return False
            
            doc, similarity = results_with_scores[0]
            
            cleaned_query_text = query_text[:100].replace('\n', ' ')
            logger.debug(f"Verificação de duplicidade semântica: Similaridade com o mais próximo = {similarity:.4f} (limiar: {threshold}) para o documento começando com '{cleaned_query_text}...'")

            return similarity >= threshold

        except Exception as e:
            logger.error(f"Erro durante a verificação de duplicidade semântica: {e}", exc_info=True)
            return False


    def rag_query(self, query: str) -> str:
        """
        Realiza uma busca RAG na base de conhecimento.
        """
        if self.vector_store is None:
            logger.warning("Tentativa de busca RAG, mas o vector store não foi inicializado.")
            return "A base de conhecimento (vector store) ainda não foi criada. Por favor, ingira documentos primeiro."
        
        try:
            # Usa o vector store como um retriever
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": self.rag_config.get('top_k_results', 3)}
            )
            # Busca por documentos relevantes
            relevant_docs = retriever.get_relevant_documents(query)

            if not relevant_docs:
                return "Nenhuma informação relevante encontrada na base de conhecimento para este tópico."

            # Formata a resposta com o conteúdo e a fonte dos documentos
            context_str = "\n\n---\n\n".join(
                [f"Fonte: {os.path.basename(doc.metadata.get('source', 'desconhecida'))}\n\nConteúdo: {doc.page_content}" for doc in relevant_docs]
            )
            return context_str
        except Exception as e:
            logger.error(f"Erro durante a consulta RAG para query '{query[:50]}...': {e}", exc_info=True)
            return f"Erro ao consultar a base de conhecimento: {e}"

# Cria uma instância única do manager para ser usada em todo o sistema
try:
    kb_manager = KnowledgeBaseManager()
except RuntimeError as e:
    logger.critical(f"Falha crítica na inicialização do KnowledgeBaseManager: {e}")
    # Em um cenário real, você pode querer que a aplicação pare aqui ou entre em um modo de falha seguro.
    kb_manager = None # Garante que a variável exista mas seja None, para que outras partes possam verificar.
