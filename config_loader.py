# config_loader.py
import yaml
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

class ConfigLoader:
    _instance = None
    _config = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path="config.yaml"):
        if self._config is None:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)

    def get_embedding_model(self):
        """Retorna a instância do modelo de embedding com base na configuração."""
        config = self._config['embedding_provider']
        provider = config['provider']
        
        if provider == "huggingface":
            print(f"Carregando modelo de embedding local: {config['model_name']}")
            return HuggingFaceEmbeddings(
                model_name=config['model_name'],
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': False}
            )
        elif provider == "google":
            print(f"Usando modelo de embedding da API Google: {config['model_name']}")
            return GoogleGenerativeAIEmbeddings(model=config['model_name'])
        else:
            raise ValueError(f"Provedor de embedding desconhecido: {provider}")

    def get_llm(self, agent_name: str):
        """Retorna uma instância de LLM para um agente específico."""
        agent_config = self._config['agent_models'].get(agent_name)
        if not agent_config:
            print(f"Configuração para '{agent_name}' não encontrada. Usando 'default'.")
            agent_config = self._config['agent_models']['default']
        
        provider = agent_config['provider']
        model_name = agent_config['model_name']
        temperature = agent_config.get('temperature', 0.2)
        
        print(f"Configurando LLM para '{agent_name}': provider={provider}, model={model_name}, temp={temperature}")

        if provider == "google":
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        # Adicione aqui outros provedores se necessário (ex: 'openai', 'anthropic')
        else:
            raise ValueError(f"Provedor de LLM desconhecido: {provider}")

# Singleton para carregar a configuração uma única vez
config = ConfigLoader()
