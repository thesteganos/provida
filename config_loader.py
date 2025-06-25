# config_loader.py
"""
Este módulo é responsável por carregar e gerenciar as configurações da aplicação
a partir de um arquivo YAML (`config.yaml`). Ele também lida com o carregamento
de variáveis de ambiente de um arquivo `.env`, como chaves de API.

Principais componentes:
- `ConfigLoader`: Uma classe Singleton que garante que as configurações sejam
  lidas do disco apenas uma vez.
- Carregamento de variáveis de ambiente com `python-dotenv`.
- Injeção de chaves de API (obtidas do ambiente) nas configurações dos modelos
  de IA para evitar armazenar segredos no arquivo YAML.
- Fornecimento de métodos para acessar seções específicas da configuração
  (LLMs, Neo4j, RAG).
"""
import yaml
import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Classe Singleton para carregar e fornecer acesso às configurações da aplicação.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = 'config.yaml'):
        # Evita reinicialização
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        load_dotenv()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.critical(f"Arquivo de configuração '{config_path}' não encontrado. A aplicação não pode continuar.")
            raise SystemExit(f"Arquivo de configuração '{config_path}' não encontrado.")
        except yaml.YAMLError as e:
            logger.critical(f"Erro ao parsear o arquivo YAML '{config_path}': {e}")
            raise SystemExit(f"Erro no formato do arquivo de configuração: {e}")

        # Injeta a chave de API nos LLMs do provedor Google
        if self._config.get('llms'):
            for agent_name, agent_config in self._config['llms'].items():
                if agent_config.get('provider') == 'google' and not agent_config.get('api_key'):
                    agent_config['api_key'] = self.google_api_key
        
        # MODIFICADO: Adicionada a lógica para injetar a chave de API também nos modelos de embedding.
        if self._config.get('models'):
            for model_type, model_config in self._config['models'].items():
                if model_config.get('provider') == 'google' and not model_config.get('api_key'):
                    model_config['api_key'] = self.google_api_key

        self._initialized = True
        logger.info(f"Configurações carregadas de '{config_path}' e variáveis de ambiente aplicadas.")

    def get_llm(self, agent_name: str) -> Optional[Any]:
        """Retorna uma instância de LLM configurada para um agente específico."""
        agent_config = self._config.get('llms', {}).get(agent_name)
        if not agent_config:
            logger.error(f"Configuração para o agente LLM '{agent_name}' não encontrada.")
            return None
        
        provider = agent_config.get('provider')
        model_name = agent_config.get('model')
        temperature = agent_config.get('temperature', 0.7)
        api_key = agent_config.get('api_key')

        if provider == "google":
            logger.info(f"Configurando LLM para '{agent_name}': provider=google, model={model_name}, temp={temperature}")
            if not api_key:
                logger.warning(f"Chave de API da Google não encontrada para o agente '{agent_name}'. A autenticação pode falhar.")
            return GoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)
        else:
            logger.error(f"Provedor de LLM '{provider}' não suportado.")
            return None

    def get_allowed_origins(self) -> List[str]:
        """Retorna a lista de origens permitidas para CORS."""
        return self._config.get('server', {}).get('allowed_origins', [])

config = ConfigLoader()
