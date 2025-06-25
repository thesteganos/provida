# config_loader.py
"""
Este módulo é responsável por carregar e gerenciar as configurações da aplicação.

Ele lê um arquivo YAML (`config.yaml` por padrão) que contém parâmetros
para modelos de linguagem (LLMs), modelos de embedding, concorrência de API,
e outras configurações específicas dos agentes e do sistema.

A classe `ConfigLoader` implementa o padrão Singleton para garantir que as
configurações sejam carregadas apenas uma vez. Ela fornece métodos para
acessar modelos de LLM e embedding configurados, além de um semáforo
para controlar a concorrência de chamadas à API do Google.

Principais funcionalidades:
- Carregamento de configurações de um arquivo YAML.
- Fornecimento de instâncias de LLMs (atualmente Google Gemini) com base na configuração.
- Fornecimento de instâncias de modelos de embedding (HuggingFace local ou Google API).
- Gerenciamento de um semáforo para chamadas assíncronas à API do Google,
  limitando o número de requisições concorrentes.
"""
import yaml
import asyncio
import logging # Adicionado logging
from typing import Union, Optional, Dict, Any # Adicionado para type hints mais específicos

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# Configuração básica do logging, pode ser ajustada no main.py ou similar para mais controle
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Gerencia o carregamento e acesso às configurações da aplicação a partir de um arquivo YAML.

    Implementa o padrão Singleton para garantir uma única instância da configuração.
    Lê o arquivo de configuração (padrão: "config.yaml") na primeira inicialização.
    Fornece métodos para obter modelos de embedding, LLMs e um semáforo para
    controlar chamadas à API do Google.

    Atributos:
        _instance (Optional[ConfigLoader]): A instância singleton da classe.
        _config (Optional[Dict[str, Any]]): O dicionário de configuração carregado do arquivo YAML.
        _google_semaphore (Optional[asyncio.Semaphore]): Semáforo para limitar
            requisições concorrentes à API do Google.
    """
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[Dict[str, Any]] = None
    _google_semaphore: Optional[asyncio.Semaphore] = None

    def __new__(cls, *args, **kwargs):
        """Garante que apenas uma instância da classe ConfigLoader seja criada (Singleton)."""
        if not cls._instance:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializa o ConfigLoader, carregando o arquivo de configuração se ainda não foi carregado.

        Args:
            config_path (str): O caminho para o arquivo de configuração YAML.
                               Padrão é "config.yaml".
        """
        if self._config is None:
            try:
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
                if self._config is None: # yaml.safe_load pode retornar None para arquivo vazio
                    logger.error(f"Arquivo de configuração '{config_path}' está vazio ou malformado.")
                    raise ValueError(f"Arquivo de configuração '{config_path}' está vazio ou malformado.")
                logger.info(f"Arquivo de configuração '{config_path}' carregado com sucesso.")
            except FileNotFoundError:
                logger.error(f"Arquivo de configuração '{config_path}' não encontrado. A aplicação não pode iniciar.")
                # Poderia carregar um dict de configuração padrão aqui se fizesse sentido
                # self._config = DEFAULT_APP_CONFIG
                raise
            except yaml.YAMLError as e:
                logger.error(f"Erro ao parsear o arquivo YAML '{config_path}': {e}")
                raise
            
            # Acesso seguro à configuração do semáforo
            api_concurrency_config = self._config.get('api_concurrency', {})
            max_requests = api_concurrency_config.get('google_max_concurrent_requests', 5) # Padrão 5 se não especificado
            self._google_semaphore = asyncio.Semaphore(max_requests)
            logger.info(f"Semáforo da API Google inicializado com {max_requests} requisições simultâneas.")

    def get_embedding_model(self) -> Union[HuggingFaceEmbeddings, GoogleGenerativeAIEmbeddings]:
        """
        Retorna uma instância do modelo de embedding configurado.

        Lê a seção 'embedding_provider' do arquivo de configuração para determinar
        qual modelo de embedding instanciar (HuggingFace local ou Google API).
        Os `model_kwargs` e `encode_kwargs` para HuggingFace podem ser estendidos
        para serem configuráveis via `config.yaml` para maior flexibilidade.

        Returns:
            Union[HuggingFaceEmbeddings, GoogleGenerativeAIEmbeddings]: Instância do modelo.

        Raises:
            ValueError: Se o provedor de embedding ou as configurações necessárias
                        não forem encontradas ou forem inválidas.
        """
        embedding_config = self._config.get('embedding_provider')
        if not embedding_config or not isinstance(embedding_config, dict):
            logger.error("Configuração 'embedding_provider' ausente ou malformada no config.yaml.")
            raise ValueError("Configuração 'embedding_provider' ausente ou malformada.")

        provider = embedding_config.get('provider')
        model_name = embedding_config.get('model_name')

        if not provider or not model_name:
            logger.error("Chaves 'provider' ou 'model_name' ausentes em 'embedding_provider'.")
            raise ValueError("Chaves 'provider' ou 'model_name' ausentes em 'embedding_provider'.")

        if provider == "huggingface":
            logger.info(f"Carregando modelo de embedding local HuggingFace: {model_name}")
            # Sugestão: model_kwargs e encode_kwargs poderiam ser lidos do config.yaml
            # Ex: model_kwargs = embedding_config.get('model_kwargs', {'device': 'cpu'})
            # Ex: encode_kwargs = embedding_config.get('encode_kwargs', {'normalize_embeddings': False})
            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=embedding_config.get('model_kwargs', {'device': 'cpu'}), # Permite configuração
                encode_kwargs=embedding_config.get('encode_kwargs', {'normalize_embeddings': False}) # Permite configuração
            )
        elif provider == "google":
            logger.info(f"Usando modelo de embedding da API Google: {model_name}")
            return GoogleGenerativeAIEmbeddings(model=model_name)
        else:
            logger.error(f"Provedor de embedding desconhecido: {provider}")
            raise ValueError(f"Provedor de embedding desconhecido: {provider}")

    def get_llm(self, agent_name: str) -> ChatGoogleGenerativeAI:
        """
        Retorna uma instância de um Large Language Model (LLM) configurado para um agente específico.

        Lê a seção 'agent_models' da configuração. Se uma configuração específica
        para `agent_name` existir, ela é usada; caso contrário, a configuração 'default'
        é utilizada. Atualmente, suporta apenas o provedor "google" (Google Gemini).

        Args:
            agent_name (str): O nome do agente para o qual o LLM está sendo solicitado.

        Returns:
            ChatGoogleGenerativeAI: Uma instância do LLM configurado.

        Raises:
            ValueError: Se o provedor de LLM ou as configurações necessárias
                        não forem encontradas ou forem inválidas.
        """
        agent_models_config = self._config.get('agent_models')
        if not agent_models_config or not isinstance(agent_models_config, dict):
            logger.error("Configuração 'agent_models' ausente ou malformada no config.yaml.")
            raise ValueError("Configuração 'agent_models' ausente ou malformada.")

        default_llm_config = agent_models_config.get('default')
        if not default_llm_config:
            logger.error("Configuração 'default' para LLM ausente em 'agent_models'.")
            raise ValueError("Configuração 'default' para LLM ausente em 'agent_models'.")

        agent_config = agent_models_config.get(agent_name, default_llm_config)

        provider = agent_config.get('provider')
        model_name = agent_config.get('model_name')
        temperature = agent_config.get('temperature', 0.2) # Padrão 0.2 se não especificado

        if not provider or not model_name:
            logger.error(f"Configuração 'provider' ou 'model_name' ausente para o agente '{agent_name}' ou no default.")
            raise ValueError(f"Configuração 'provider' ou 'model_name' ausente para o agente '{agent_name}'.")

        logger.info(f"Configurando LLM para '{agent_name}': provider={provider}, model={model_name}, temp={temperature}")
        if provider == "google":
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        # Adicionar 'elif provider == "openai":' etc. aqui para outros provedores
        else:
            logger.error(f"Provedor de LLM desconhecido: {provider}")
            raise ValueError(f"Provedor de LLM desconhecido: {provider}")

    async def throttled_google_acall(self, llm_chain: Any, input_data: Dict[str, Any]) -> Any:
        """
        Executa uma chamada assíncrona a uma cadeia de LLM (llm_chain) de forma controlada.

        Utiliza o `_google_semaphore` para limitar o número de chamadas concorrentes
        à API do Google, conforme configurado em 'api_concurrency.google_max_concurrent_requests'.
        Este método é específico para o semáforo do Google. Se outros provedores
        necessitarem de throttling, uma abordagem mais genérica pode ser necessária.

        Args:
            llm_chain (Any): A cadeia LangChain (ou similar) que será invocada.
                             Espera-se que tenha um método `ainvoke`.
            input_data (Dict[str, Any]): Os dados de entrada para a cadeia `llm_chain`.

        Returns:
            Any: O resultado da invocação da cadeia `llm_chain`.
        """
        if self._google_semaphore is None:
            # Isso não deveria acontecer se __init__ for chamado corretamente.
            logger.error("Semáforo do Google não inicializado antes da chamada.")
            # Decidir como tratar: levantar erro ou prosseguir sem throttling?
            # Por segurança, levantar erro pode ser melhor para alertar sobre um problema de inicialização.
            raise RuntimeError("Semáforo do Google não inicializado.")

        async with self._google_semaphore:
            return await llm_chain.ainvoke(input_data)

config = ConfigLoader()
"""Instância global (Singleton) do ConfigLoader para fácil acesso em toda a aplicação."""
