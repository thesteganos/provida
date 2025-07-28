"""Helper utilities to interact with the Neo4j database."""

import logging
from functools import lru_cache
from typing import Any, Dict, List

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config.settings import Neo4jDatabaseSettings as Neo4jSettings

logger = logging.getLogger(__name__)


@lru_cache
def get_neo4j_driver(settings: Neo4jSettings) -> AsyncDriver:
    """
    Retorna um driver assíncrono do Neo4j em cache para as configurações fornecidas.

    Este driver é usado para interagir com o banco de dados Neo4j. A função utiliza
    `lru_cache` para garantir que apenas uma instância do driver seja criada para
    um dado conjunto de configurações, otimizando o uso de recursos.

    Args:
        settings (Neo4jSettings): Um objeto de configurações contendo URI, usuário e senha do Neo4j.

    Returns:
        AsyncDriver: Uma instância do driver assíncrono do Neo4j.

    Raises:
        Exception: Se houver uma falha ao criar o driver Neo4j.
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


async def execute_query(
    driver: AsyncDriver, database: str, query: str, parameters: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    """
    Executa uma consulta Cypher no banco de dados Neo4j especificado.

    Esta função assíncrona executa uma query Cypher e retorna os resultados.
    Ela inclui tratamento de erros para falhas na execução da consulta.

    Args:
        driver (AsyncDriver): Instância do driver retornada por `get_neo4j_driver`.
        database (str): Nome do banco de dados no qual a consulta será executada.
        query (str): A string da consulta Cypher.
        parameters (Dict[str, Any], optional): Parâmetros da consulta passados para o Neo4j. Padrão é None.

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários, onde cada dicionário representa um registro da consulta.

    Raises:
        Exception: Se houver um erro durante a execução da consulta.
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
