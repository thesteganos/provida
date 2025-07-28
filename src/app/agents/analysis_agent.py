import json
import logging
import hashlib

from app.agents.memory_agent import MemoryAgent
from app.core.llm_provider import llm_provider
from app.config.settings import settings
from app.models.analysis_models import AnalysisResult
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AnalysisAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.analysis_agent)
        self.memory = MemoryAgent(agent_id="analysis_agent")

    async def classify_evidence(self, text: str) -> AnalysisResult:
        """
        Analyzes the provided text to extract a summary, classify its evidence
        level (A, B, C, D, E), and identify relevant keywords.

        This method now serves a dual purpose: classification for immediate use and
        data extraction for populating the knowledge graph, as required by the
        KnowledgeGraphAgent.

        Args:
            text (str): The text to classify.

        Returns:
            Dict[str, Any]: A dictionary containing the classified evidence level and justification.
        """
        # Gera um hash do texto para usar como chave única na memória
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        recalled_data_str = await self.memory.recall(key=text_hash)

        if recalled_data_str:
            logger.info(f"Classification for text hash {text_hash[:10]}... recalled from memory.")
            try:
                # Se encontrou na memória, retorna o resultado salvo
                return AnalysisResult(**json.loads(recalled_data_str))
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode recalled memory for hash {text_hash[:10]}... Re-classifying.")

        # Se não encontrou na memória, prossegue com a classificação
        from app.prompts.llm_prompts import ANALYSIS_AGENT_PROMPT

        prompt = ANALYSIS_AGENT_PROMPT.format(text=text)

        try:
            response = await self.model.generate_content_async(prompt)
            # Limpa a resposta do LLM para extrair o JSON de forma mais robusta
            cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")
            classification_data = AnalysisResult(**json.loads(cleaned_text))

            # Armazena a nova classificação na memória para uso futuro
            await self.memory.remember(key=text_hash, value=json.dumps(classification_data))

            return classification_data
        except json.JSONDecodeError as e:
            logger.error(
                f"Falha ao decodificar JSON da resposta do LLM: {e}\nResposta: {response.text}",
                exc_info=True
            )
            return AnalysisResult(summary="Falha ao analisar a classificação.", evidence_level="E", justification="Resposta JSON inválida do modelo", keywords=[])
        except Exception as e:
            logger.error(f"Erro inesperado durante a classificação de evidência: {e}", exc_info=True)
            return AnalysisResult(summary="Ocorreu um erro inesperado.", evidence_level="E", justification=f"Erro inesperado: {str(e)}", keywords=[])
