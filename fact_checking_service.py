import logging
from typing import Any, Dict

from app.agents.claim_extraction_agent import ClaimExtractionAgent
from app.agents.verification_agent import VerificationAgent

logger = logging.getLogger(__name__)


async def verify_text_against_kg(text: str) -> Dict[str, Any]:
    """
    Orquestra o processo completo de verificação de fatos de um texto.

    1. Extrai alegações factuais do texto.
    2. Verifica cada alegação contra o grafo de conhecimento.
    3. Retorna um relatório de verificação detalhado.
    """
    logger.info("Iniciando o serviço de verificação de fatos...")

    # Passo 1: Extrair alegações
    claim_extractor = ClaimExtractionAgent()
    claims = await claim_extractor.extract_claims(text)

    if not claims:
        logger.info("Nenhuma alegação factual extraída. Verificação concluída.")
        return {"hallucination_detected": False, "message": "Nenhuma alegação factual para verificar."}

    # Passo 2: Verificar alegações
    verifier = VerificationAgent()
    report = await verifier.bulk_verify(claims)
    logger.info(f"Verificação concluída. Alegações não verificadas: {report['unverified_count']}")
    return report