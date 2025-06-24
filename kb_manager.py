# kb_manager.py
"""
Este módulo gerencia a base de conhecimento da aplicação PROVIDA.

Ele é responsável por interagir com o banco de dados de grafos (Neo4j) e
o banco de dados vetorial (FAISS) para armazenamento e recuperação de informações.
A classe `KnowledgeBaseManager` implementa o padrão Singleton e centraliza
as operações de:
- Conexão com Neo4j para dados estruturados de pacientes e conhecimento médico.
- Criação, carregamento e atualização do índice vetorial FAISS para busca RAG
  a partir de documentos (PDFs, TXTs).
- Ingestão de novos documentos, incluindo pré-processamento, divisão de texto,
  geração de embeddings e deduplicação (por hash de conteúdo e similaridade semântica).
- Consulta à base RAG para encontrar evidências textuais.
- Adição de dados de pacientes ao Neo4j.

Utiliza o `ConfigLoader` para obter configurações de modelos de embedding e RAG.
Também lida com o logging de hashes de conteúdo para evitar reprocessamento.
"""
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
    """
    Gerencia a base de conhecimento híbrida (Neo4j e FAISS/RAG).

    Implementa o padrão Singleton para garantir uma única instância.
    Responsável por:
    - Conectar-se ao Neo4j.
    - Carregar ou criar o índice vetorial FAISS.
    - Gerenciar o processo de ingestão de novos documentos (PDF, TXT),
      incluindo carregamento, divisão, embedding, e deduplicação.
    - Fornecer métodos para consultar o RAG e adicionar dados ao Neo4j.

    Atributos:
        graph (Optional[Neo4jGraph]): Instância do conector Neo4j. None se a conexão falhar.
        embeddings (any): Modelo de embedding carregado (ex: HuggingFaceEmbeddings).
        vectorstore_path (str): Caminho para o diretório do índice FAISS.
        sources_dir (str): Diretório base para as fontes de conhecimento.
        content_hash_log (str): Caminho para o arquivo de log de hashes de conteúdo processado.
        content_hashes (set): Conjunto de hashes de conteúdo já processados.
        vectorstore (FAISS): Instância do banco de dados vetorial FAISS.
        retriever (VectorStoreRetriever): Retriever LangChain para consultas RAG.
        initialized (bool): Flag para indicar se a inicialização foi concluída.
    """
    _instance = None

    def __init__(self):
        """
        Inicializa o KnowledgeBaseManager.

        Configura a conexão com o Neo4j, carrega/cria o vectorstore FAISS,
        inicializa o modelo de embeddings e o retriever RAG.
        A inicialização ocorre apenas na primeira vez que a instância é criada.
        """
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
            except ServiceUnavailable as e:
                logging.error(f"Serviço Neo4j indisponível em {os.getenv('NEO4J_URI')}: {e}. O grafo de conhecimento não estará funcional.")
            except Exception as e:
                logging.error(f"Erro inesperado ao conectar com Neo4j: {e}", exc_info=True)

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
        """Garante que apenas uma instância da classe KnowledgeBaseManager seja criada (Singleton)."""
        if not cls._instance:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
        return cls._instance

    def _get_processed_hashes(self) -> set:
        """
        Carrega os hashes de conteúdo de documentos já processados a partir de um arquivo de log.

        Returns:
            set: Um conjunto de strings de hash. Retorna um conjunto vazio se o arquivo
                 de log não existir.
        """
        if not os.path.exists(self.content_hash_log):
            return set()
        with open(self.content_hash_log, 'r') as f:
            return set(line.strip() for line in f)

    def _log_content_hash(self, content_hash: str):
        """
        Adiciona um hash de conteúdo ao arquivo de log e ao conjunto em memória.

        Args:
            content_hash (str): O hash SHA256 do conteúdo do documento.
        """
        with open(self.content_hash_log, 'a') as f:
            f.write(f"{content_hash}\n")
        self.content_hashes.add(content_hash)

    def _generate_content_hash(self, documents: list) -> str:
        """
        Gera um hash SHA256 para o conteúdo combinado de uma lista de documentos LangChain.

        Args:
            documents (list): Uma lista de objetos Document LangChain.
                              O conteúdo de `page_content` de cada documento é concatenado.

        Returns:
            str: O hash SHA256 hexadecimal do conteúdo.
        """
        full_text = "".join(doc.page_content for doc in documents).encode('utf-8')
        return hashlib.sha256(full_text).hexdigest()

    def _is_semantically_duplicate(self, documents: list, threshold: float = 0.98) -> bool:
        """
        Verifica se um novo documento é semanticamente similar a documentos existentes no vectorstore.

        Compara o primeiro documento da lista de entrada com os `k=1` vizinhos mais próximos
        no índice FAISS. A similaridade é calculada a partir da distância L2.

        Args:
            documents (list): Lista de documentos LangChain a serem verificados.
                              Apenas o primeiro documento é usado para a busca de similaridade.
            threshold (float): O limiar de similaridade (0.0 a 1.0) acima do qual um documento
                               é considerado uma duplicata semântica. Padrão é 0.98.

        Returns:
            bool: True se uma duplicata semântica for encontrada, False caso contrário.
        """
        if not documents or self.vectorstore.index.ntotal == 0:
            return False
        query_text = documents[0].page_content
        similar_docs_with_scores = self.vectorstore.similarity_search_with_score(query_text, k=1)
        if similar_docs_with_scores:
            score = similar_docs_with_scores[0][1] # FAISS score is L2 distance
            # Convert L2 distance to similarity (0-1 range). This formula is common.
            similarity = 1 - (score**2 / 2)
            if similarity > threshold:
                print(f"Potencial duplicado semântico encontrado com similaridade de {similarity:.4f}.")
                return True
        return False

    def _load_or_create_vectorstore(self) -> FAISS:
        """
        Carrega um índice FAISS existente do disco ou cria um novo se não existir.

        Se `self.vectorstore_path` existir, carrega o índice. Caso contrário, chama
        `_create_vectorstore_from_scratch()` para construir um novo índice a partir
        dos documentos em `self.sources_dir`.

        Returns:
            FAISS: A instância carregada ou recém-criada do índice FAISS.
        """
        if os.path.exists(self.vectorstore_path):
            print(f"Carregando VectorStore existente de '{self.vectorstore_path}'...")
            return FAISS.load_local(self.vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            print("Nenhum VectorStore encontrado. Criando um novo do zero...")
            return self._create_vectorstore_from_scratch()

    def _create_vectorstore_from_scratch(self) -> FAISS:
        """
        Cria um novo índice FAISS a partir de documentos em `self.sources_dir`.

        Carrega documentos PDF e TXT, os divide em chunks, gera embeddings e
        constrói o índice FAISS. Salva o índice no disco e registra os hashes
        de conteúdo dos documentos processados.

        Returns:
            FAISS: A instância recém-criada do índice FAISS. Retorna um índice com
                   um placeholder se nenhum documento for encontrado.
        """
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
        """
        Processa e ingere um novo documento na base de conhecimento RAG.

        O processo inclui:
        1. Carregar o conteúdo do arquivo (PDF ou TXT).
        2. Gerar um hash do conteúdo para deduplicação primária.
        3. Verificar duplicidade semântica com documentos existentes.
        4. Dividir o documento em chunks.
        5. Adicionar os chunks (com seus embeddings) ao índice FAISS.
        6. Salvar o índice atualizado e registrar o hash do novo conteúdo.

        Args:
            file_path (str): O caminho para o arquivo do documento a ser ingerido.

        Returns:
            str: Uma mensagem indicando o resultado da ingestão (sucesso, erro, duplicata).
        """
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
        """
        Adiciona ou atualiza os dados de um paciente no grafo Neo4j.

        Usa uma query Cypher MERGE para criar um nó :Patient se não existir,
        ou atualizar suas propriedades se já existir.

        Args:
            patient_id (str): O identificador único do paciente.
            data (dict): Um dicionário contendo as propriedades do paciente a serem
                         adicionadas ou atualizadas.
        """
        if self.graph:
            try:
                self.graph.query("MERGE (p:Patient {id: $patient_id}) SET p += $props", params={"patient_id": patient_id, "props": data})
                logging.info(f"Dados para o paciente {patient_id} adicionados/atualizados no Neo4j.")
            except Exception as e:
                logging.error(f"Falha ao adicionar dados do paciente {patient_id} ao Neo4j: {e}", exc_info=True)
        else:
            logging.warning(f"Neo4j indisponível. Não foi possível adicionar/atualizar dados para o paciente {patient_id}.")

    def rag_query(self, query: str) -> str:
        """
        Realiza uma consulta na base de conhecimento RAG (FAISS).

        Utiliza o `self.retriever` para buscar documentos relevantes para a consulta.
        Formata os resultados, incluindo a fonte (nome do arquivo) e o conteúdo do documento.

        Args:
            query (str): A string de consulta para a busca RAG.

        Returns:
            str: Uma string contendo os resultados formatados da busca.
                 Retorna "Nenhuma informação relevante encontrada..." se nenhum
                 documento for encontrado.
        """
        docs = self.retriever.invoke(query)
        if not docs: return "Nenhuma informação relevante encontrada na base de conhecimento."
        return "\n\n---\n\n".join([f"Fonte: {os.path.basename(doc.metadata.get('source', 'N/A'))}\n\n{doc.page_content}" for doc in docs])

kb_manager = KnowledgeBaseManager()
"""Instância global (Singleton) do KnowledgeBaseManager para fácil acesso em toda a aplicação."""
