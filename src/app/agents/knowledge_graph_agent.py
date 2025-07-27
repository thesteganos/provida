import logging
from typing import Dict, Any

from app.config.settings import settings
from app.core.db.neo4j_manager import execute_query, get_neo4j_driver

logger = logging.getLogger(__name__)


class KnowledgeGraphAgent:
    """
    Agente responsável por interagir com o grafo de conhecimento no Neo4j.
    """

    def __init__(self):
        if not settings.database.neo4j_knowledge:
            raise ValueError(
                "Configurações do Neo4j para o grafo de conhecimento não definidas."
            )

        self.db_settings = settings.database.neo4j_knowledge
        self.driver = get_neo4j_driver(self.db_settings)

    async def update_graph_with_analysis(
        self,
        source_identifier: str,
        analysis_data: Dict[str, Any],
        research_topic: str,
    ):
        """
        Atualiza o grafo de conhecimento com os resultados de uma análise.

        Cria/atualiza nós para a Fonte, o Tópico, a Evidência, o Resumo e as Palavras-chave,
        e estabelece as relações entre eles.
        """
        # Extrai os dados necessários da análise.
        # Supõe-se que o AnalysisAgent fornecerá esses campos.
        summary = analysis_data.get("summary")
        evidence_level = analysis_data.get("evidence_level")
        keywords = analysis_data.get("keywords", [])

        if not all([summary, evidence_level]):
            logger.warning(
                f"Dados de análise incompletos para a fonte {source_identifier}. "
                "É necessário 'summary' e 'evidence_level'."
            )
            return None

        query = """
        MERGE (topic:Topic {name: $research_topic})
        MERGE (source:Source {identifier: $source_identifier})
        MERGE (source)-[:RELATED_TO]->(topic)

        MERGE (summary:Summary {text: $summary, source_id: $source_identifier})
        MERGE (source)-[:CONTAINS]->(summary)

        MERGE (evidence:EvidenceLevel {level: $evidence_level})
        MERGE (summary)-[:HAS_EVIDENCE]->(evidence)

        WITH summary
        UNWIND $keywords as keyword_name
        MERGE (kw:Keyword {name: keyword_name})
        MERGE (summary)-[:MENTIONS]->(kw)
        """
        parameters = {
            "source_identifier": source_identifier,
            "research_topic": research_topic,
            "summary": summary,
            "evidence_level": evidence_level,
            "keywords": keywords,
        }

        try:
            await execute_query(self.driver, self.db_settings.database, query, parameters)
            logger.info(f"Grafo de conhecimento atualizado para a fonte '{source_identifier}'.")
        except Exception as e:
            logger.error(f"Falha ao atualizar o grafo de conhecimento para a fonte '{source_identifier}': {e}")
            raise