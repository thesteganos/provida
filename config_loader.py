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
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

class ConfigLoader:
    """
    Gerencia o carregamento e acesso às configurações da aplicação a partir de um arquivo YAML.

    Implementa o padrão Singleton para garantir uma única instância da configuração.
    Lê o arquivo de configuração (padrão: "config.yaml") na primeira inicialização.
    Fornece métodos para obter modelos de embedding, LLMs e um semáforo para
    controlar chamadas à API do Google.

    Atributos:
        _instance (Optional[ConfigLoader]): A instância singleton da classe.
        _config (Optional[dict]): O dicionário de configuração carregado do arquivo YAML.
        _google_semaphore (Optional[asyncio.Semaphore]): Semáforo para limitar
            requisições concorrentes à API do Google.
    """
    _instance = None
    _config = None
    _google_semaphore = None

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
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            max_requests = self._config.get('api_concurrency', {}).get('google_max_concurrent_requests', 5)
            self._google_semaphore = asyncio.Semaphore(max_requests)
            print(f"Semáforo da API Google inicializado com {max_requests} requisições simultâneas.")

    def get_embedding_model(self) -> any:
        """
        Retorna uma instância do modelo de embedding configurado.

        Lê a seção 'embedding_provider' do arquivo de configuração para determinar
        qual modelo de embedding instanciar (HuggingFace local ou Google API).

        Returns:
            any: Uma instância de `HuggingFaceEmbeddings` ou `GoogleGenerativeAIEmbeddings`.

        Raises:
            ValueError: Se o provedor de embedding especificado na configuração
                        não for reconhecido.
        """
        config = self._config['embedding_provider']
        provider = config['provider']
        if provider == "huggingface":
            print(f"Carregando modelo de embedding local: {config['model_name']}")
            return HuggingFaceEmbeddings(
                model_name=config['model_name'], model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': False}
            )
        elif provider == "google":
            print(f"Usando modelo de embedding da API Google: {config['model_name']}")
            return GoogleGenerativeAIEmbeddings(model=config['model_name'])
        else:
            raise ValueError(f"Provedor de embedding desconhecido: {provider}")

    def get_llm(self, agent_name: str) -> ChatGoogleGenerativeAI:
        """
        Retorna uma instância de um Large Language Model (LLM) configurado para um agente específico.

        Lê a seção 'agent_models' da configuração. Se uma configuração específica
        para `agent_name` existir, ela é usada; caso contrário, a configuração 'default'
        é utilizada. Atualmente, suporta apenas o provedor "google" (Google Gemini).

        Args:
            agent_name (str): O nome do agente para o qual o LLM está sendo solicitado.
                              Usado para buscar configurações específicas de modelo e temperatura.

        Returns:
            ChatGoogleGenerativeAI: Uma instância do LLM configurado.

        Raises:
            ValueError: Se o provedor de LLM especificado na configuração não for "google"
                        ou se a configuração do agente não for encontrada.
        """
        agent_config = self._config['agent_models'].get(agent_name, self._config['agent_models']['default'])
        provider = agent_config['provider']
        model_name = agent_config['model_name']
        temperature = agent_config.get('temperature', 0.2)
        print(f"Configurando LLM para '{agent_name}': provider={provider}, model={model_name}, temp={temperature}")
        if provider == "google":
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        else:
            raise ValueError(f"Provedor de LLM desconhecido: {provider}")

    async def throttled_google_acall(self, llm_chain: any, input_data: dict) -> any:
        """
        Executa uma chamada assíncrona a uma cadeia de LLM (llm_chain) de forma controlada.

        Utiliza o `_google_semaphore` para limitar o número de chamadas concorrentes
        à API do Google, conforme configurado em 'api_concurrency.google_max_concurrent_requests'.

        Args:
            llm_chain (any): A cadeia LangChain (ou similar) que será invocada.
                             Espera-se que tenha um método `ainvoke`.
            input_data (dict): Os dados de entrada para a cadeia `llm_chain`.

        Returns:
            any: O resultado da invocação da cadeia `llm_chain`.
        """
        async with self._google_semaphore:
            return await llm_chain.ainvoke(input_data)

config = ConfigLoader()
"""Instância global (Singleton) do ConfigLoader para fácil acesso em toda a aplicação."""
