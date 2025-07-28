"""Helper utilities to interact with the Neo4j database."""

import logging
from functools import lru_cache
from typing import Any, Dict, List

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.models.config_models import Neo4jSettings

logger = logging.getLogger(__name__)


@lru_cache
def get_neo4j_driver(settings: Neo4jSettings) -> AsyncDriver:
    """Return a cached ``AsyncDriver`` for the given settings."""
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


async def execute_query(
    driver: AsyncDriver, database: str, query: str, parameters: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    """Run a Cypher query on the specified database.

    Parameters
    ----------
    driver : AsyncDriver
        Driver instance returned by :func:`get_neo4j_driver`.
    database : str
        Name of the database in which to execute the query.
    query : str
        Cypher query string.
    parameters : dict, optional
        Query parameters passed to Neo4j.

    Returns
    -------
    list[dict]
        Query records converted to dictionaries.
    """
    parameters = parameters or {}
    try:
        records, summary, _ = await driver.execute_query(
            query, parameters, database_=database
        )
        logger.debug("Consulta executada no DB '%s': %s", database, summary.query)
        return [record.data() for record in records]
    except Exception as e:
        logger.error("Erro ao executar a consulta no DB '%s': %s", database, e, exc_info=True)
        raise
