import json
import logging

from app.agents.memory_agent import MemoryAgent
from app.core.llm_provider import llm_provider
from app.config.settings import settings
from app.models.analysis_models import AnalysisResult
from app.agents.utils import extract_json_from_response
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AnalysisAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.analysis_agent)
        self.memory = MemoryAgent(agent_id="analysis_agent")

    async def classify_evidence(self, text: str, source_identifier: str) -> AnalysisResult:
        """
        Analisa o texto fornecido para extrair um resumo, classificar seu nível de evidência
        e identificar palavras-chave relevantes. Usa um identificador de fonte para cache.

        Args:
            text (str): O texto a ser classificado.
            source_identifier (str): O identificador único da fonte (ex: URL) para cache.

        Returns:
            AnalysisResult: Um objeto Pydantic contendo os dados da análise.
        """
        # Usa o source_identifier como chave de cache, que é mais estável e eficiente.
        recalled_data_str = await self.memory.recall(key=source_identifier)

        if recalled_data_str:
            logger.info(f"Análise para a fonte '{source_identifier}' recuperada da memória.")
            try:
                return AnalysisResult(**json.loads(recalled_data_str))
            except json.JSONDecodeError:
                logger.warning(f"Falha ao decodificar memória para a fonte '{source_identifier}'. Reanalisando.")

        from app.prompts.llm_prompts import ANALYSIS_AGENT_PROMPT
        prompt = ANALYSIS_AGENT_PROMPT.format(text=text)

        try:
            response = await self.model.generate_content_async(prompt)
            classification_dict = extract_json_from_response(response.text)
            classification_data = AnalysisResult(**classification_dict)

            # Armazena o resultado na memória usando o source_identifier.
            await self.memory.remember(key=source_identifier, value=classification_data.model_dump_json())

            return classification_data
        except ValueError as e: # Captura o erro do extract_json_from_response
            logger.error(
                f"Falha ao extrair JSON da resposta do LLM para a fonte '{source_identifier}': {e}",
                exc_info=True
            )
            return AnalysisResult(summary="Falha ao analisar a classificação.", evidence_level="E", justification="Resposta JSON inválida do modelo", keywords=[])
        except Exception as e:
            logger.error(f"Erro inesperado durante a classificação para a fonte '{source_identifier}': {e}", exc_info=True)
            return AnalysisResult(summary="Ocorreu um erro inesperado.", evidence_level="E", justification=f"Erro inesperado: {str(e)}", keywords=[])
