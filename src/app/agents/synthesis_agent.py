import json
import logging

from app.core.llm_provider import llm_provider
from app.config.settings import settings
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SynthesisAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings.models.synthesis_agent)

    async def generate_summary_with_citations(self, text: str, research_question: str, sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generates a summary with sentence-level citations.

        Args:
            text (str): The text to summarize.
            research_question (str): The research question the summary should address.
            sources (List[Dict[str, str]]): A list of dictionaries, each containing 'id' and 'content' of the source.

        Returns:
            Dict[str, Any]: A dictionary containing the summary and extracted citations.
        """
        # Format sources for the prompt
        formatted_sources = ""
        for source in sources:
            formatted_sources += f"ID: {source['id']}\nContent: {source['content']}\n\n"

        prompt = f"""Você é um Agente de Síntese e Citação. Sua tarefa é gerar um resumo conciso e informativo do texto fornecido, respondendo à pergunta de pesquisa. Para cada frase no resumo que utilize informação do texto original, você DEVE incluir uma citação no formato [ID_DA_FONTE].

        Texto para Resumir:
        --- TEXTO ORIGINAL ---
        {text}
        --- FIM DO TEXTO ORIGINAL ---

        Fontes Disponíveis:
        --- FONTES ---
        {formatted_sources}
        --- FIM DAS FONTES ---

        Pergunta de Pesquisa: {research_question}

        Formato de Saída (JSON):
        {{
            "summary": "Seu resumo com citações [ID_DA_FONTE]",
            "citations_used": [
                {{
                    "id": "ID_DA_FONTE",
                    "sentence_in_summary": "Frase do resumo que usa esta fonte"
                }}
            ]
        }}

        Certifique-se de que a saída seja um JSON válido e completo. Se uma frase no resumo não puder ser diretamente rastreada a uma fonte fornecida, não inclua uma citação para ela.
        """

        try:
            import json
            summary_data = json.loads(response.text)
            return summary_data
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {"error": str(e), "summary": "", "citations_used": []}