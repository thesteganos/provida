# config_loader.py
import yaml
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

class ConfigLoader:
    _instance = None
    _config = None
    _google_semaphore = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path="config.yaml"):
        if self._config is None:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            max_requests = self._config.get('api_concurrency', {}).get('google_max_concurrent_requests', 5)
            self._google_semaphore = asyncio.Semaphore(max_requests)
            print(f"Semáforo da API Google inicializado com {max_requests} requisições simultâneas.")

    def get_embedding_model(self):
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

    def get_llm(self, agent_name: str):
        agent_config = self._config['agent_models'].get(agent_name, self._config['agent_models']['default'])
        provider = agent_config['provider']
        model_name = agent_config['model_name']
        temperature = agent_config.get('temperature', 0.2)
        print(f"Configurando LLM para '{agent_name}': provider={provider}, model={model_name}, temp={temperature}")
        if provider == "google":
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        else:
            raise ValueError(f"Provedor de LLM desconhecido: {provider}")

    async def throttled_google_acall(self, llm_chain, input_data):
        async with self._google_semaphore:
            return await llm_chain.ainvoke(input_data)

config = ConfigLoader()
