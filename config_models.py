from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ModelsSettings(BaseSettings):
    """Configurações para os modelos de LLM."""

    planning_agent: str = "gemini-1.5-pro-latest"
    analysis_agent: str = "gemini-1.5-pro-latest"
    synthesis_agent: str = "gemini-1.5-pro-latest"
    rag_agent: str = "gemini-1.5-flash-latest"


class ChromaSettings(BaseSettings):
    """Configurações para o ChromaDB."""

    host: str = "localhost"
    port: int = 8000
    collection: str = "provida_knowledge"


class DatabaseSettings(BaseSettings):
    """Configurações para os bancos de dados."""

    chroma: ChromaSettings = Field(default_factory=ChromaSettings)


class AppSettings(BaseSettings):
    """
    Configurações globais da aplicação, carregadas de variáveis de ambiente.
    """

    google_api_key: str
    brave_api_key: Optional[str] = None
    entrez_email: Optional[str] = None
    entrez_api_key: Optional[str] = None

    llm_provider: str = "google"
    models: ModelsSettings = Field(default_factory=ModelsSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")