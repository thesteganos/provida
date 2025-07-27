import logging
from typing import Any, Dict, List

from app.config.settings import settings
from app.core.db.neo4j_manager import execute_query, get_neo4j_driver

logger = logging.getLogger(__name__)


class VerificationAgent:
    """
    Agente responsável por verificar fatos contra o grafo de conhecimento.
    """

    def __init__(self):
        if not settings.database.neo4j_knowledge:
            raise ValueError("Configurações do Neo4j para conhecimento não definidas.")
        self.db_settings = settings.database.neo4j_knowledge
        self.driver = get_neo4j_driver(self.db_settings)

    async def verify_claim(self, claim: Dict[str, str]) -> bool:
        """
        Verifica uma única alegação no grafo de conhecimento.
        Retorna True se um caminho correspondente for encontrado.
        """
        # Esta consulta é uma simplificação. Um sistema de produção poderia ter uma
        # lógica mais complexa para mapear predicados para tipos de relação
        # e buscar em diferentes tipos de nós.
        query = """
        MATCH (s)-[r]->(o)
        WHERE (toLower(s.name) = toLower($subject) OR toLower(s.identifier) = toLower($subject) OR toLower(s.text) = toLower($subject))
          AND (toLower(o.name) = toLower($object) OR toLower(o.identifier) = toLower($object) OR toLower(o.text) = toLower($object))
          AND toLower(type(r)) CONTAINS toLower($predicate)
        RETURN count(r) > 0 AS verified
        """
        # Simplificando o predicado para uma busca mais flexível
        simple_predicate = claim.get("predicate", "").replace("_", " ").split(" ")[-1]

        parameters = {
            "subject": claim.get("subject"),
            "predicate": simple_predicate,
            "object": claim.get("object"),
        }

        try:
            result = await execute_query(self.driver, self.db_settings.database, query, parameters)
            return result[0].get("verified", False) if result else False
        except Exception:
            return False

    async def bulk_verify(self, claims: List[Dict[str, str]]) -> Dict[str, Any]:
        """Verifica uma lista de alegações e retorna um relatório."""
        verified_claims = []
        unverified_claims = []

        for claim in claims:
            is_verified = await self.verify_claim(claim)
            (verified_claims if is_verified else unverified_claims).append(claim)

        hallucination_detected = len(unverified_claims) > 0
        return {
            "hallucination_detected": hallucination_detected,
            "verified_count": len(verified_claims),
            "unverified_count": len(unverified_claims),
            "verified_claims": verified_claims,
            "unverified_claims": unverified_claims,
        }