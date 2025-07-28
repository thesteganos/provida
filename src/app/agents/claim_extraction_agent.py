import json
import logging
from typing import Any, Dict, List

from app.config.settings import settings
from app.core.llm_provider import llm_provider
from app.models.verification_models import Claim # Importar o modelo Claim
from pydantic import parse_obj_as # Importar parse_obj_as

logger = logging.getLogger(__name__)


class ClaimExtractionAgent:
    """
    Agente responsável por extrair alegações factuais (tripletas) de um texto.
    """

    def __init__(self):
        self.model = llm_provider.get_model(settings.models.claim_extraction_agent)

    async def extract_claims(self, text: str) -> List[Claim]: # Alterar tipo de retorno
        """
        Deconstrói um texto em uma lista de tripletas (sujeito, predicado, objeto).
        """
        prompt = f"""
        Você é um agente de análise linguística. Sua tarefa é extrair todas as alegações factuais do texto fornecido.
        Cada alegação deve ser representada como uma triplera JSON com "subject", "predicate" e "object".
        O "predicate" deve ser uma frase verbal concisa em maiúsculas, representando a relação (ex: 'IS_A', 'CAUSES', 'TREATS', 'HAS_COMPLICATION').

        Exemplo:
        Texto de entrada: "A gastrectomia vertical, um tipo de cirurgia bariátrica, pode causar fístulas."
        Saída JSON esperada:
        [
            {{"subject": "gastrectomia vertical", "predicate": "IS_A", "object": "cirurgia bariátrica"}},
            {{"subject": "gastrectomia vertical", "predicate": "CAN_CAUSE", "object": "fístulas"}}
        ]

        --- TEXTO PARA ANÁLISE ---
        {text}
        --- FIM DO TEXTO ---

        Sua resposta DEVE ser um array JSON válido. Se nenhuma alegação for encontrada, retorne um array vazio [].
        """
        try:
            response = await self.model.generate_content_async(prompt)
            cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")
            claims = parse_obj_as(List[Claim], json.loads(cleaned_text)) # Validar com Pydantic
            logger.info(f"{len(claims)} alegações extraídas do texto.")
            return claims
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Falha ao decodificar JSON ou validar alegações: {e}\nResposta: {response.text}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado na extração de alegações: {e}", exc_info=True)
            return []
