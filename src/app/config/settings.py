import os
import yaml
from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Define Pydantic models mirroring config.yaml structure

class AppSettings(BaseModel):
    name: str
    version: str
    debug: bool

class Neo4jDatabaseSettings(BaseModel):
    uri: str
    user: str
    password: str
    database: str

class Neo4jSettingsGroup(BaseModel):
    knowledge: Neo4jDatabaseSettings
    memory_agents: Neo4jDatabaseSettings

class ChromaSettings(BaseModel):
    host: str = "localhost"
    port: int = 8000
    collection: str = "provida_knowledge"

class DatabaseSettings(BaseModel):
    neo4j: Neo4jSettingsGroup
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)

class MinioSettings(BaseModel):
    access_key: str
    secret_key: str
    endpoint: str

class GoogleSettings(BaseModel):
    api_key: str

class LLMModelSettings(BaseModel):
    enabled: bool
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    timeout: int

class ModelsSettings(BaseModel):
    llm: LLMModelSettings
    planning_agent: Optional[str] = None
    analysis_agent: Optional[str] = None
    synthesis_agent: Optional[str] = None
    rag_agent: Optional[str] = None
    claim_extraction_agent: Optional[str] = None

class SearchSettings(BaseModel):
    deep_search_limit: int
    timeout: int
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    rate_limit: int
    # models: ModelsSettings # Removido daqui

class ReportingSettings(BaseModel):
    enabled: bool
    interval: int
    formats: List[str]
    output_path: str

class AutomationTask(BaseModel):
    name: str
    description: str
    enabled: bool

class AutomationSettings(BaseModel):
    enabled: bool
    interval: int
    daily_update_cron: str
    quarterly_review_cron: str
    tasks: List[AutomationTask]

class GlobalSettings(BaseModel):
    app: AppSettings
    database: DatabaseSettings
    minio: MinioSettings
    google: GoogleSettings
    search: SearchSettings
    reporting: ReportingSettings
    automation: AutomationSettings
    llm_models: ModelsSettings
    
    # Adicionados de config_models.py
    brave_api_key: Optional[str] = None
    entrez_email: Optional[str] = None
    entrez_api_key: Optional[str] = None
    llm_provider: str = "google"

@lru_cache
def get_settings() -> GlobalSettings:
    """
    Carrega as configurações do arquivo config.yaml e variáveis de ambiente.
    As configurações são cacheadas para evitar leituras repetidas.
    """
    config_path = Path(__file__).parent.parent.parent.parent / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Replace environment variables in config_data
    def replace_env_vars(data):
        if isinstance(data, dict):
            return {k: replace_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [replace_env_vars(elem) for elem in data]
        elif isinstance(data, str):
            # Use regex to find ${VAR_NAME} and replace with os.getenv
            import re
            return re.sub(r'\$\{([^}]+)\}', lambda m: os.getenv(m.group(1), m.group(0)), data)
        return data

    processed_config_data = replace_env_vars(config_data)
    
    # Ajustar a estrutura para o modelo GlobalSettings
    # Mover 'models' de 'search' para 'llm_models'
    if 'search' in processed_config_data and 'models' in processed_config_data['search']:
        processed_config_data['llm_models'] = processed_config_data['search'].pop('models')

    return GlobalSettings(**processed_config_data)

settings = get_settings()