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
    language_agent: Optional[str] = None

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
    tasks: Optional[List[AutomationTask]] = None # Make tasks optional

class FileOutputSettings(BaseModel):
    enabled: bool
    path: str
    max_bytes: int
    backup_count: int

class SystemLogSettings(BaseModel):
    enabled: bool
    path: str
    level: str

class LoggingSettings(BaseModel):
    level: str
    console_output: bool
    file_output: FileOutputSettings
    system_log: SystemLogSettings

class RagSettings(BaseModel):
    n_results: int

class GlobalSettings(BaseModel):
    app: AppSettings
    database: DatabaseSettings
    minio: MinioSettings
    google: GoogleSettings
    rag: RagSettings
    search: SearchSettings
    reporting: ReportingSettings
    automation: AutomationSettings
    logging: LoggingSettings # Add logging settings
    llm_models: ModelsSettings # This is already handled in get_settings to be moved here

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

    # Handle optional 'tasks' in automation
    if 'automation' in processed_config_data and 'tasks' not in processed_config_data['automation']:
        processed_config_data['automation']['tasks'] = None

    return GlobalSettings(**processed_config_data)

settings = get_settings()