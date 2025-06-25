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
# import shutil # Não utilizado diretamente, mas pode ser útil no futuro para manipulação de arquivos
import hashlib
import logging
from typing import Set, List, Optional, Any # Adicionado para type hints

from langchain_core.documents import Document # Adicionado para type hint
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_community.embeddings.base import Embeddings # Para type hint de self.embeddings

# Tentar importar exceções específicas do Neo4j para captura mais granular
try:
    from neo4j.exceptions import ServiceUnavailable, AuthError # type: ignore
except ImportError:
    # Fallback para uma exceção genérica se as específicas não estiverem disponíveis
    # (embora geralmente estejam com o driver neo4j instalado)
    ServiceUnavailable = Exception # type: ignore
    AuthError = Exception # type: ignore

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config_loader import config # Importa a instância singleton do ConfigLoader

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

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
        embeddings (Embeddings): Modelo de embedding carregado.
        vectorstore_path (str): Caminho para o diretório do índice FAISS.
        sources_dir (str): Diretório base para as fontes de conhecimento.
        content_hash_log (str): Caminho para o arquivo de log de hashes de conteúdo processado.
        content_hashes (Set[str]): Conjunto de hashes de conteúdo já processados.
        vectorstore (FAISS): Instância do banco de dados vetorial FAISS.
        retriever (Any): Retriever LangChain para consultas RAG (tipo específico depende do vectorstore).
        initialized (bool): Flag para indicar se a inicialização foi concluída.
    """
    _instance: Optional['KnowledgeBaseManager'] = None
    graph: Optional[Neo4jGraph]
    embeddings: Embeddings
    vectorstore_path: str
    sources_dir: str
    content_hash_log: str
    content_hashes: Set[str]
    vectorstore: FAISS
    retriever: Any # Langchain retrievers podem variar, FAISS.as_retriever() retorna VectorStoreRetriever
    initialized: bool = False


    def __new__(cls, *args: Any, **kwargs: Any) -> 'KnowledgeBaseManager':
        """Garante que apenas uma instância da classe KnowledgeBaseManager seja criada (Singleton)."""
        if not cls._instance:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Inicializa o KnowledgeBaseManager.

        Configura a conexão com o Neo4j, carrega/cria o vectorstore FAISS,
        inicializa o modelo de embeddings e o retriever RAG.
        A inicialização ocorre apenas na primeira vez que a instância é criada.
        """
        # hasattr é mais seguro para checar se o atributo foi definido na instância,
        # especialmente em cenários de re-inicialização ou herança complexa.
        # No entanto, para um Singleton simples como este, self.initialized funciona bem.
        if not self.initialized:
            logger.info("Inicializando o Gerenciador da Base de Conhecimento (KnowledgeBaseManager)...")
            self.graph = None # Inicializa como None

            # Verificação das variáveis de ambiente para Neo4j
            neo4j_uri = os.getenv("NEO4J_URI")
            neo4j_user = os.getenv("NEO4J_USERNAME")
            neo4j_pass = os.getenv("NEO4J_PASSWORD")

            if not neo4j_uri:
                logger.warning("Variável de ambiente NEO4J_URI não definida. Conexão com Neo4j será pulada.")
            elif not neo4j_user: # Assume-se que user e pass são necessários se URI estiver presente
                logger.warning("Variável de ambiente NEO4J_USERNAME não definida. Conexão com Neo4j será pulada.")
            elif not neo4j_pass:
                logger.warning("Variável de ambiente NEO4J_PASSWORD não definida. Conexão com Neo4j será pulada.")
            else:
                try:
                    self.graph = Neo4jGraph(url=neo4j_uri, username=neo4j_user, password=neo4j_pass)
                    self.graph.query("RETURN 1") # Tenta uma query simples para verificar a conexão
                    logger.info(f"Conexão com Neo4j estabelecida com sucesso em {neo4j_uri}.")
                except AuthError as e:
                    logger.error(f"Erro de autenticação com Neo4j ({neo4j_uri}): {e}. Verifique suas credenciais.")
                    self.graph = None # Garante que graph seja None em caso de falha
                except ServiceUnavailable as e:
                    logger.error(f"Serviço Neo4j indisponível em {neo4j_uri}: {e}. O grafo de conhecimento não estará funcional.")
                    self.graph = None
                except Exception as e: # Captura outras exceções potenciais da conexão
                    logger.error(f"Erro inesperado ao conectar com Neo4j ({neo4j_uri}): {e}", exc_info=True)
                    self.graph = None

            self.embeddings = config.get_embedding_model()
            self.vectorstore_path = "./faiss_index"
            self.sources_dir = "./knowledge_sources" # Diretório para PDFs, TXTs, etc.
            # Nome de arquivo de log de hash mais descritivo
            self.content_hash_log = os.path.join(self.sources_dir, "processed_document_content_hashes.log")
            
            os.makedirs(self.sources_dir, exist_ok=True) # Garante que o diretório de fontes exista
            self.content_hashes = self._get_processed_hashes()
            self.vectorstore = self._load_or_create_vectorstore()
            
            # Acesso seguro à configuração RAG
            rag_config = config._config.get('rag_config', {})
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": rag_config.get('top_k_results', 3)}
            )
            self.initialized = True
            logger.info("Gerenciador da Base de Conhecimento pronto.")

    def _get_processed_hashes(self) -> Set[str]:
        """
        Carrega os hashes de conteúdo de documentos já processados a partir de um arquivo de log.

        Returns:
            Set[str]: Um conjunto de strings de hash. Retorna um conjunto vazio se o arquivo
                      de log não existir ou não puder ser lido.
        """
        if not os.path.exists(self.content_hash_log):
            return set()
        try:
            with open(self.content_hash_log, 'r', encoding='utf-8') as f:
                # Garante que apenas linhas não vazias sejam adicionadas ao conjunto
                return set(line.strip() for line in f if line.strip())
        except IOError as e:
            logger.error(f"Erro ao ler o arquivo de log de hashes '{self.content_hash_log}': {e}")
            return set()

    def _log_content_hash(self, content_hash: str) -> None:
        """
        Adiciona um hash de conteúdo ao arquivo de log e ao conjunto em memória.

        Args:
            content_hash (str): O hash SHA256 do conteúdo do documento.
        """
        try:
            # Abre o arquivo em modo 'append' com encoding utf-8
            with open(self.content_hash_log, 'a', encoding='utf-8') as f:
                f.write(f"{content_hash}\n")
            self.content_hashes.add(content_hash)
        except IOError as e:
            logger.error(f"Erro ao escrever no arquivo de log de hashes '{self.content_hash_log}': {e}")

    def _generate_content_hash(self, documents: List[Document]) -> str:
        """
        Gera um hash SHA256 para o conteúdo combinado de uma lista de documentos LangChain.
        Cada Document na lista pode representar uma página de um PDF ou um arquivo TXT inteiro.

        Args:
            documents (List[Document]): Uma lista de objetos Document LangChain.
                                        O conteúdo de `page_content` de cada documento é concatenado.

        Returns:
            str: O hash SHA256 hexadecimal do conteúdo.
        """
        # Concatena o page_content de todos os Document objects na lista
        full_text = "".join(doc.page_content for doc in documents).encode('utf-8')
        return hashlib.sha256(full_text).hexdigest()

    def _is_semantically_duplicate(self, documents: List[Document], threshold: float) -> bool:
        """
        Verifica se um novo documento é semanticamente similar a documentos existentes no vectorstore.

        Compara o primeiro documento da lista de entrada (que pode ser a primeira página de um PDF)
        com os `k=1` vizinhos mais próximos no índice FAISS. A similaridade é calculada
        a partir da distância L2.

        A fórmula de conversão de distância L2 para similaridade (1 - (score^2 / 2))
        é uma heurística comum, especialmente para embeddings normalizados, onde
        score^2 é a distância Euclidiana quadrada. Para uma robustez maior, o limiar (threshold)
        deve ser configurável e testado.

        Args:
            documents (List[Document]): Lista de documentos LangChain a serem verificados.
                                        Apenas o primeiro documento é usado para a busca de similaridade.
            threshold (float): O limiar de similaridade (0.0 a 1.0) acima do qual um documento
                               é considerado uma duplicata semântica.

        Returns:
            bool: True se uma duplicata semântica for encontrada, False caso contrário ou em erro.
        """
        if not documents or not hasattr(self.vectorstore, 'index') or self.vectorstore.index.ntotal == 0:
            return False # Não há o que comparar ou o índice está vazio

        # Usa o conteúdo do primeiro Documento da lista para a query de similaridade.
        # Para PDFs, este será o conteúdo da primeira página.
        query_text = documents[0].page_content

        try:
            # k=1 para encontrar o vizinho mais próximo.
            similar_docs_with_scores: List[tuple[Document, float]] = self.vectorstore.similarity_search_with_score(query_text, k=1)

            if similar_docs_with_scores:
                # score é a distância L2. Quanto menor, mais similar.
                score = similar_docs_with_scores[0][1]
                # Converte distância L2 para similaridade (0-1 range).
                # Esta fórmula é comum para embeddings normalizados: similaridade_cosseno = 1 - (distancia_euclidiana^2 / 2)
                similarity = 1 - (score**2 / 2)

                logger.debug(f"Verificação de duplicidade semântica: Similaridade com o mais próximo = {similarity:.4f} (limiar: {threshold}) para o documento começando com '{query_text[:100].replace('\n', ' ')}...'")
                if similarity > threshold:
                    logger.info(f"Potencial duplicado semântico encontrado com similaridade de {similarity:.4f} (acima do limiar de {threshold}).")
                    return True
        except Exception as e:
            logger.error(f"Erro durante a verificação de duplicidade semântica: {e}", exc_info=True)
            # Em caso de erro na verificação, opta-se por não considerar como duplicado para não impedir a ingestão.
            return False
        return False

    def _load_or_create_vectorstore(self) -> FAISS:
        """
        Carrega um índice FAISS existente do disco ou cria um novo se não existir.
        Se o carregamento falhar ou o diretório estiver incompleto, tenta recriar.

        Returns:
            FAISS: A instância carregada ou recém-criada do índice FAISS.
        """
        # Verifica se o caminho existe, é um diretório, e contém os arquivos de índice esperados.
        if os.path.exists(self.vectorstore_path) and \
           os.path.isdir(self.vectorstore_path) and \
           os.path.exists(os.path.join(self.vectorstore_path, "index.faiss")) and \
           os.path.exists(os.path.join(self.vectorstore_path, "index.pkl")):
            logger.info(f"Carregando VectorStore FAISS existente de '{self.vectorstore_path}'...")
            try:
                # allow_dangerous_deserialization é necessário para LangChain FAISS.
                # Implica confiança nos arquivos de índice.
                return FAISS.load_local(
                    self.vectorstore_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                logger.error(f"Falha ao carregar VectorStore de '{self.vectorstore_path}': {e}. Tentando recriar do zero.", exc_info=True)
                # Se o carregamento falhar (ex: índice corrompido), prossegue para recriar.
                # Opcionalmente, poderia deletar o índice antigo aqui antes de recriar.
        elif os.path.exists(self.vectorstore_path) and not (os.path.exists(os.path.join(self.vectorstore_path, "index.faiss")) and os.path.exists(os.path.join(self.vectorstore_path, "index.pkl"))):
             logger.warning(f"Diretório VectorStore '{self.vectorstore_path}' existe mas está incompleto ou não é um índice FAISS válido. Tentando recriar.")

        logger.info("Nenhum VectorStore FAISS válido encontrado ou carregamento falhou. Criando um novo do zero...")
        return self._create_vectorstore_from_scratch()

    def _create_vectorstore_from_scratch(self) -> FAISS:
        """
        Cria um novo índice FAISS a partir de documentos em `self.sources_dir`.

        Carrega documentos PDF e TXT, os divide em chunks, gera embeddings e
        constrói o índice FAISS. Salva o índice no disco e registra os hashes
        de conteúdo dos documentos processados.

        Returns:
            FAISS: A instância recém-criada do índice FAISS. Retorna um índice com
                   um placeholder se nenhum documento for encontrado ou em caso de erro crítico.
        """
        logger.info(f"Lendo documentos de '{self.sources_dir}' para criação do VectorStore...")

        # `autodetect_encoding=True` para TextLoader pode ajudar com diferentes encodings.
        # `silent_errors=True` no DirectoryLoader loga erros de arquivos individuais mas continua.
        loader = DirectoryLoader(
            self.sources_dir,
            glob="**/*[.pdf,.txt]", # Procura em subdiretórios também
            loader_cls=lambda p: PyPDFLoader(p) if p.lower().endswith('.pdf') else TextLoader(p, autodetect_encoding=True),
            show_progress=True,
            use_multithreading=True, # Pode acelerar o carregamento
            silent_errors=True # Loga erros de arquivos individuais mas continua o processo
        )

        try:
            # `source_documents` aqui são os documentos originais, um Document por página (PDF) ou um por arquivo (TXT).
            source_documents: List[Document] = loader.load()
        except Exception as e: # Erro crítico no DirectoryLoader
            logger.error(f"Erro crítico durante o carregamento de documentos do diretório '{self.sources_dir}': {e}", exc_info=True)
            source_documents = [] # Procede com lista vazia para criar placeholder DB

        if not source_documents:
            logger.warning("Nenhum documento encontrado ou carregado para indexar. Criando VectorStore com placeholder.")
            # Criar um índice com um placeholder evita que self.vectorstore seja None.
            placeholder_db = FAISS.from_texts(["placeholder_document_for_empty_index"], self.embeddings)
            try:
                placeholder_db.save_local(self.vectorstore_path)
            except Exception as e_save: # Captura qualquer erro ao salvar
                logger.error(f"Falha ao salvar o VectorStore placeholder (nenhum documento): {e_save}", exc_info=True)
            return placeholder_db

        # Configurações de RAG para text splitting
        rag_cfg = config._config.get('rag_config', {})
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_cfg.get('chunk_size', 1000),
            chunk_overlap=rag_cfg.get('chunk_overlap', 200)
        )
        # `docs_for_indexing` são os chunks que serão efetivamente adicionados ao FAISS
        docs_for_indexing: List[Document] = text_splitter.split_documents(source_documents)
        
        if not docs_for_indexing: # Se, após o split, não houver chunks
            logger.warning("Nenhum chunk gerado a partir dos documentos carregados. Verifique o conteúdo dos arquivos e as configurações do text_splitter.")
            placeholder_db = FAISS.from_texts(["placeholder_document_no_chunks_generated"], self.embeddings)
            try:
                placeholder_db.save_local(self.vectorstore_path)
            except Exception as e_save:
                logger.error(f"Falha ao salvar o VectorStore placeholder (sem chunks): {e_save}", exc_info=True)
            return placeholder_db

        logger.info(f"Indexando {len(docs_for_indexing)} chunks de {len(source_documents)} documentos de origem...")
        try:
            db = FAISS.from_documents(docs_for_indexing, self.embeddings)
            db.save_local(self.vectorstore_path)
            logger.info(f"VectorStore FAISS salvo em '{self.vectorstore_path}'.")
        except Exception as e: # Erro ao criar ou salvar o índice FAISS
            logger.error(f"Falha ao criar ou salvar o VectorStore FAISS: {e}", exc_info=True)
            # Retorna um DB placeholder em caso de falha na criação/salvamento do principal
            placeholder_db = FAISS.from_texts(["placeholder_document_creation_failed"], self.embeddings)
            try: # Tenta salvar o placeholder, mas não é crítico se falhar
                placeholder_db.save_local(self.vectorstore_path)
            except Exception as e_save_ph:
                logger.error(f"Falha crítica ao salvar até mesmo o VectorStore placeholder: {e_save_ph}", exc_info=True)
            return placeholder_db # Retorna o placeholder mesmo que não consiga salvar
        
        # Limpa e re-registra os hashes dos documentos que foram efetivamente indexados
        try:
            # Limpa o arquivo de log de hashes antes de repopular
            with open(self.content_hash_log, 'w', encoding='utf-8') as f:
                pass # Simplesmente abre e fecha em modo 'w' para truncar
        except IOError as e_io:
            logger.warning(f"Não foi possível limpar o arquivo de log de hashes '{self.content_hash_log}': {e_io}")

        # Agrupa os Document objects por source_path para gerar o hash do arquivo original completo
        content_by_source_path: dict[str, list[str]] = {}
        for doc_obj in source_documents: # Iterar sobre os documentos originais (pré-chunking)
            source_path = doc_obj.metadata.get('source')
            if not source_path: # Segurança: pula se não houver source metadata
                logger.warning(f"Documento sem 'source' nos metadados durante o hash logging: {doc_obj.page_content[:100].replace('\n',' ')}...")
                continue

            if source_path not in content_by_source_path:
                content_by_source_path[source_path] = []
            content_by_source_path[source_path].append(doc_obj.page_content)
            
        for source_file_path, page_contents_list in content_by_source_path.items():
            # Cria um Document temporário com todo o conteúdo do arquivo para gerar o hash
            # Passa uma lista de Document para _generate_content_hash
            full_file_documents = [Document(page_content="".join(page_contents_list), metadata={'source': source_file_path})]
            file_content_hash = self._generate_content_hash(full_file_documents)
            self._log_content_hash(file_content_hash)
        logger.info(f"{len(content_by_source_path)} hashes de arquivos de origem registrados após criação do VectorStore.")
        
        return db

    def ingest_new_document(self, file_path: str) -> str:
        """
        Processa e ingere um novo documento na base de conhecimento RAG.

        Inclui carregamento, deduplicação por hash e semântica, divisão,
        adição ao índice FAISS e registro do hash do conteúdo original do arquivo.

        Args:
            file_path (str): O caminho para o arquivo do documento a ser ingerido.

        Returns:
            str: Uma mensagem indicando o resultado da ingestão.
        """
        filename = os.path.basename(file_path)
        logger.info(f"Iniciando ingestão do documento: '{filename}' de '{file_path}'")

        try:
            # `autodetect_encoding=True` para TextLoader; PyPDFLoader para PDFs
            loader = PyPDFLoader(file_path) if filename.lower().endswith('.pdf') else TextLoader(file_path, autodetect_encoding=True)
            # `original_documents` é uma lista de Document (um por página para PDF, um para TXT)
            original_documents: List[Document] = loader.load()
        except FileNotFoundError: # Erro específico se o arquivo não for encontrado
            logger.error(f"Arquivo '{filename}' não encontrado em '{file_path}' para ingestão.")
            return f"Erro: Arquivo '{filename}' não encontrado."
        except Exception as e: # Outros erros de leitura do arquivo
            logger.error(f"Erro ao ler o documento '{filename}': {e}", exc_info=True)
            return f"Erro ao ler o documento '{filename}': {e}"

        if not original_documents: # Se loader.load() retornar lista vazia
            logger.warning(f"Documento '{filename}' está vazio ou não pôde ser carregado (nenhum Document LangChain gerado).")
            return f"Documento '{filename}' está vazio ou não pôde ser carregado."

        # 1. Deduplicação por hash do conteúdo completo do arquivo
        # `original_documents` já é uma lista de Document, um por página (PDF) ou um por TXT.
        # `_generate_content_hash` concatena o page_content de todos eles.
        content_hash = self._generate_content_hash(original_documents)
        if content_hash in self.content_hashes:
            logger.info(f"DEDUPLICAÇÃO POR HASH: O conteúdo de '{filename}' (hash: {content_hash}) já existe.")
            return f"DEDUPLICAÇÃO POR HASH: O conteúdo de '{filename}' já existe."

        # 2. Deduplicação semântica
        # O limiar para _is_semantically_duplicate pode ser configurável via config.yaml
        rag_cfg_sem = config._config.get('rag_config', {})
        semantic_threshold = rag_cfg_sem.get('semantic_deduplication_threshold', 0.98) # Pega do config ou usa padrão

        # `_is_semantically_duplicate` usa o primeiro Document da lista `original_documents` para a query.
        # Para PDFs com múltiplas páginas, isso significa comparar com base na primeira página.
        # Isto pode ser uma limitação para PDFs onde a primeira página não é representativa.
        # Uma estratégia melhor poderia ser embeddar o documento inteiro ou uma amostra representativa,
        # mas isso aumentaria a complexidade e o tempo de processamento.
        # Por ora, a lógica existente é mantida com este comentário.
        if self._is_semantically_duplicate(original_documents, threshold=semantic_threshold):
            logger.info(f"DEDUPLICAÇÃO SEMÂNTICA: O conteúdo de '{filename}' é muito similar a um já existente (limiar: {semantic_threshold}).")
            return f"DEDUPLICAÇÃO SEMÂNTICA: O conteúdo de '{filename}' é muito similar a um já existente."

        # 3. Divisão do documento em chunks para indexação
        rag_cfg_split = config._config.get('rag_config', {})
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_cfg_split.get('chunk_size', 1000),
            chunk_overlap=rag_cfg_split.get('chunk_overlap', 200)
        )
        # `docs_for_indexing` são os chunks que serão efetivamente adicionados ao FAISS
        docs_for_indexing: List[Document] = text_splitter.split_documents(original_documents)
        
        if not docs_for_indexing: # Se, após o split, não houver chunks
            logger.warning(f"Documento '{filename}' resultou em zero chunks após o split. Nada a indexar. Verifique o conteúdo e o chunk_size.")
            return f"Documento '{filename}' não pôde ser dividido em chunks para indexação (conteúdo muito pequeno ou problema no splitter)."

        # 4. Adicionar ao VectorStore e salvar
        try:
            self.vectorstore.add_documents(docs_for_indexing)
            self.vectorstore.save_local(self.vectorstore_path) # Salva o índice atualizado
            self._log_content_hash(content_hash) # Loga o hash do conteúdo do arquivo original
            logger.info(f"Documento '{filename}' ingerido e indexado com sucesso ({len(docs_for_indexing)} chunks). Hash: {content_hash}")
            return f"Documento '{filename}' ingerido e indexado com sucesso."
        except Exception as e: # Erro ao adicionar ao FAISS ou salvar
            logger.error(f"Erro ao adicionar/salvar documento '{filename}' no VectorStore: {e}", exc_info=True)
            # O hash não foi logado se a falha ocorreu antes de _log_content_hash.
            # Se _log_content_hash fosse chamado antes, seria necessário um mecanismo de rollback do hash.
            # A lógica atual chama _log_content_hash *após* o sucesso do save_local, o que é mais seguro.
            return f"Erro ao indexar o documento '{filename}': {e}"


    def add_patient_data(self, patient_id: str, data: dict) -> None:
        """
        Adiciona ou atualiza os dados de um paciente no grafo Neo4j.

        Usa uma query Cypher MERGE para criar um nó :Patient se não existir,
        ou atualizar suas propriedades se já existir.

        Args:
            patient_id (str): O identificador único do paciente.
            data (dict): Um dicionário contendo as propriedades do paciente a serem
                         adicionadas ou atualizadas.
        """
        if self.graph: # Verifica se a conexão com Neo4j existe
            try:
                # Usar parâmetros na query é mais seguro e geralmente mais performático
                self.graph.query(
                    "MERGE (p:Patient {id: $patient_id}) SET p += $props",
                    params={"patient_id": patient_id, "props": data}
                )
                logger.info(f"Dados para o paciente '{patient_id}' adicionados/atualizados no Neo4j.")
            except Exception as e: # Captura exceções genéricas da query Neo4j
                logger.error(f"Falha ao adicionar/atualizar dados do paciente '{patient_id}' ao Neo4j: {e}", exc_info=True)
        else: # Se self.graph for None
            logger.warning(f"Neo4j indisponível. Não foi possível adicionar/atualizar dados para o paciente '{patient_id}'.")

    def rag_query(self, query: str) -> str:
        """
        Realiza uma consulta na base de conhecimento RAG (FAISS).

        Utiliza o `self.retriever` para buscar documentos relevantes para a consulta.
        Formata os resultados, incluindo a fonte (nome do arquivo) e o conteúdo do documento.

        Args:
            query (str): A string de consulta para a busca RAG.

        Returns:
            str: Uma string contendo os resultados formatados da busca.
                 Retorna uma mensagem específica se nenhum documento for encontrado,
                 se o índice contiver apenas o placeholder, ou em caso de erro.
        """
        # Verificação de segurança para garantir que o retriever e seu método invoke existam
        if not hasattr(self.retriever, 'invoke') or not callable(getattr(self.retriever, 'invoke', None)):
            logger.error("Retriever não está configurado corretamente ou não possui método 'invoke' chamável.")
            return "Erro: Sistema de busca não está configurado corretamente."
        try:
            docs: List[Document] = self.retriever.invoke(query)

            # Lista de textos de placeholder conhecidos
            placeholder_texts = [
                "placeholder_document_for_empty_index",
                "placeholder_document_no_chunks_generated",
                "placeholder_document_creation_failed"
            ]
            # Checa se os documentos retornados são apenas um dos placeholders
            if docs and len(docs) == 1 and docs[0].page_content in placeholder_texts:
                logger.info(f"Consulta RAG por '{query[:100]}...' retornou apenas um placeholder do índice: '{docs[0].page_content}'.")
                return "A base de conhecimento textual ainda não possui documentos relevantes para consulta ou está em estado de placeholder."

            if not docs: # Se a busca não retornar nenhum documento
                logger.info(f"Nenhuma informação relevante encontrada na base de conhecimento para a query: '{query[:100]}...'")
                return "Nenhuma informação relevante encontrada na base de conhecimento."

            # Formata os resultados
            results = []
            for doc_item in docs:
                source = os.path.basename(doc_item.metadata.get('source', 'N/A'))
                page_info = f", Página: {doc_item.metadata.get('page')}" if doc_item.metadata.get('page') is not None else ""
                # Limita o tamanho do page_content para evitar respostas excessivamente longas, se necessário
                # content_preview = doc_item.page_content[:1000] + "..." if len(doc_item.page_content) > 1000 else doc_item.page_content
                results.append(f"Fonte: {source}{page_info}\n\n{doc_item.page_content}")

            return "\n\n---\n\n".join(results)

        except Exception as e: # Captura qualquer erro durante a invocação do retriever ou formatação
            logger.error(f"Erro durante a consulta RAG para '{query[:100]}...': {e}", exc_info=True)
            return f"Erro ao processar sua consulta na base de conhecimento: {e}"


kb_manager = KnowledgeBaseManager()
"""Instância global (Singleton) do KnowledgeBaseManager para fácil acesso em toda a aplicação."""
