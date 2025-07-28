import logging
from typing import List

from pydantic import ValidationError, parse_obj_as

from app.agents.utils import extract_json_from_response
from app.config.settings import settings
from app.core.llm_provider import llm_provider
from app.models.verification_models import Claim

logger = logging.getLogger(__name__)


class ClaimExtractionAgent:
    """
    Agente responsável por extrair alegações factuais (tripletas) de um texto.
    """

    def __init__(self):
        self.model = llm_provider.get_model(settings.models.claim_extraction_agent)

    async def extract_claims(self, text: str) -> List[Claim]:
        """
        Deconstrói um texto em uma lista de tripletas (sujeito, predicado, objeto).
        """
        from app.prompts.llm_prompts import CLAIM_EXTRACTION_AGENT_PROMPT

        prompt = CLAIM_EXTRACTION_AGENT_PROMPT.format(text=text)
        try:
            response = await self.model.generate_content_async(prompt)
            claims_json = extract_json_from_response(response.text)
            # A saída esperada é uma lista de objetos, então o Pydantic precisa validar cada um.
            claims = parse_obj_as(List[Claim], claims_json)
            logger.info(f"{len(claims)} alegações extraídas do texto.")
            return claims
        except (ValueError, ValidationError) as e:
            logger.error(f"Falha ao extrair ou validar alegações: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Erro inesperado na extração de alegações: {e}", exc_info=True)
            return []
