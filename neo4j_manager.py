import logging
from functools import lru_cache

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.models.config_models import Neo4jSettings

logger = logging.getLogger(__name__)


@lru_cache
def get_neo4j_driver(settings: Neo4jSettings) -> AsyncDriver:
    """
    Cria e retorna uma instância singleton do driver Neo4j.
    A instância é cacheada com base nas configurações para reutilização.
    """
    try:
        driver = AsyncGraphDatabase.driver(
            settings.uri, auth=(settings.user, settings.password)
        )
        logger.info(f"Driver Neo4j criado para a URI: {settings.uri}")
        return driver
    except Exception as e:
        logger.critical(
            f"Falha ao criar o driver Neo4j para {settings.uri}: {e}", exc_info=True
        )
        raise


async def execute_query(driver: AsyncDriver, database: str, query: str, parameters: dict = None):
    """
    Executa uma consulta Cypher no banco de dados especificado.
    """
    parameters = parameters or {}
    try:
        records, summary, _ = await driver.execute_query(
            query, parameters, database_=database
        )
        logger.debug(f"Consulta executada no DB '{database}': {summary.query}")
        return [record.data() for record in records]
    except Exception as e:
        logger.error(f"Erro ao executar a consulta no DB '{database}': {e}", exc_info=True)
        raise