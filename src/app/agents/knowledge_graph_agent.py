import logging
from typing import Any, Dict

from app.config.settings import settings
from app.core.db.neo4j_manager import execute_query, get_neo4j_driver
from app.models.agent_models import AnalysisResult

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
        analysis_data_dict: Dict[str, Any],
        research_topic: str,
    ):
        """
        Atualiza o grafo de conhecimento com os resultados de uma análise.

        Cria/atualiza nós para a Fonte, o Tópico, a Evidência, o Resumo e as Palavras-chave,
        e estabelece as relações entre eles, após validar os dados com Pydantic.
        """
        # 1. Validação robusta dos dados de entrada usando Pydantic.
        analysis_result = AnalysisResult.model_validate(analysis_data_dict)

        query = """
        // 1. Encontra ou cria os nós principais: Tópico, Fonte e Nível de Evidência.
        MERGE (topic:Topic {name: $research_topic})
        MERGE (source:Source {identifier: $source_identifier})
        MERGE (evidence:EvidenceLevel {level: $evidence_level})

        // 2. Garante que a Fonte esteja relacionada ao Tópico.
        MERGE (source)-[:RELATED_TO]->(topic)

        // 3. Faz o MERGE do Resumo no contexto da Fonte.
        //    Isso garante que um Resumo com o mesmo texto não seja duplicado para a mesma Fonte.
        //    ON CREATE define as propriedades apenas se o nó for criado.
        //    ON MATCH pode ser usado para atualizar propriedades se o nó já existir.
        MERGE (summary:Summary {text: $summary, source_identifier: $source_identifier})

        // 4. Garante que as conexões do Resumo com a Fonte, Tópico e Evidência existam.
        MERGE (source)-[:CONTAINS]->(summary)
        MERGE (topic)-[:HAS_SUMMARY]->(summary)
        MERGE (summary)-[:HAS_EVIDENCE]->(evidence)

        // 5. Processa e conecta todas as palavras-chave ao Resumo.
        //    O UNWIND + MERGE é uma maneira idempotente de garantir que todas as palavras-chave
        //    sejam conectadas sem criar duplicatas.
        WITH summary
        UNWIND $keywords as keyword_name
        MERGE (kw:Keyword {name: keyword_name})
        MERGE (summary)-[:MENTIONS]->(kw)
        """
        parameters = {
            "source_identifier": source_identifier,
            "research_topic": research_topic,
            "summary": analysis_result.summary,
            "evidence_level": analysis_result.evidence_level,
            "keywords": analysis_result.keywords,
        }

        try:
            await execute_query(self.driver, self.db_settings.database, query, parameters)
            logger.info(f"Grafo de conhecimento atualizado para a fonte '{source_identifier}'.")
        except Exception as e:
            logger.error(f"Falha ao atualizar o grafo de conhecimento para a fonte '{source_identifier}': {e}")
            raise