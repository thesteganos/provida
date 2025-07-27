import logging

from app.config.settings import settings
from app.core.db.neo4j_manager import execute_query, get_neo4j_driver

logger = logging.getLogger(__name__)


class MemoryAgent:
    def __init__(self, agent_id: str):
        if not settings.database.neo4j_memory_agents:
            raise ValueError("Configurações do Neo4j para memória de agentes não definidas.")

        self.agent_id = agent_id
        self.db_settings = settings.database.neo4j_memory_agents
        self.driver = get_neo4j_driver(self.db_settings)

    async def remember(self, key: str, value: str):
        """
        Armazena uma memória para o agente no grafo de memória.
        Cada agente tem seu próprio nó, e as memórias são conectadas a ele.
        """
        query = """
        MERGE (a:Agent {id: $agent_id})
        MERGE (m:Memory {key: $key, agent_id: $agent_id})
        SET m.value = $value, m.timestamp = timestamp()
        MERGE (a)-[:HAS_MEMORY]->(m)
        RETURN a.id as agentId, m.key as memoryKey
        """
        parameters = {"agent_id": self.agent_id, "key": key, "value": value}

        try:
            result = await execute_query(
                self.driver, self.db_settings.database, query, parameters
            )
            logger.info(f"Memória '{key}' salva para o agente '{self.agent_id}'.")
            return result
        except Exception as e:
            logger.error(f"Falha ao salvar memória para o agente '{self.agent_id}': {e}")
            return None

    async def recall(self, key: str) -> str | None:
        """
        Recupera uma memória para o agente.
        """
        query = """
        MATCH (:Agent {id: $agent_id})-[:HAS_MEMORY]->(m:Memory {key: $key})
        RETURN m.value as value
        ORDER BY m.timestamp DESC
        LIMIT 1
        """
        parameters = {"agent_id": self.agent_id, "key": key}

        try:
            result = await execute_query(
                self.driver, self.db_settings.database, query, parameters
            )
            return result[0].get("value") if result else None
        except Exception as e:
            logger.error(f"Falha ao recuperar memória para o agente '{self.agent_id}': {e}")
            return None