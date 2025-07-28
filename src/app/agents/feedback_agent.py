import logging
from typing import Dict, Any
from datetime import datetime # Import datetime here for example usage

from app.config.settings import settings
from app.core.llm_provider import llm_provider
from app.agents.memory_agent import MemoryAgent
from app.models.feedback_models import FeedbackContext, StructuredFeedback # Importar os novos modelos

logger = logging.getLogger(__name__)

class FeedbackAgent:
    """
    Agente responsável por coletar e processar feedback estruturado do usuário.
    """

    def __init__(self):
        self.model = llm_provider.get_model(settings.models.rag_agent) # Using a general LLM for feedback processing
        self.memory = MemoryAgent(agent_id="feedback_agent")
        logger.info("FeedbackAgent initialized.")

    async def collect_feedback(self, user_feedback: str, context: FeedbackContext) -> StructuredFeedback:
        """
        Processa o feedback do usuário e o estrutura usando um LLM.

        Args:
            user_feedback (str): O feedback em linguagem natural fornecido pelo usuário.
            context (FeedbackContext): Contexto relevante da interação (ex: query, resposta do agente).

        Returns:
            StructuredFeedback: Feedback estruturado (ex: sentimento, precisão, sugestões).
        """
        prompt = f"""Você é um Agente de Feedback. Sua tarefa é analisar o feedback do usuário e o contexto da interação para extrair informações estruturadas.

Contexto da Interação:
{context.model_dump_json(indent=2)}

Feedback do Usuário:
{user_feedback}

Extraia as seguintes informações em formato JSON:
- 'sentiment': Sentimento geral do feedback (positivo, negativo, neutro). Use apenas 'positivo', 'negativo' ou 'neutro'.
- 'accuracy_rating': Avaliação da precisão da resposta (escala de 1 a 5, onde 5 é muito preciso). Use um número inteiro.
- 'suggestions': Sugestões de melhoria ou novas funcionalidades (lista de strings). Use um array de strings.
- 'relevant_query': A query original à qual o feedback se refere (se identificável). Use uma string ou null.
- 'relevant_agent': O agente principal ao qual o feedback se refere (se identificável, ex: 'RAG', 'Deep Research'). Use uma string ou null.

Formato de Saída (JSON):
{{
    "sentiment": "positivo",
    "accuracy_rating": 4,
    "suggestions": ["sugestao1", "sugestao2"],
    "relevant_query": "query_original",
    "relevant_agent": "nome_do_agente"
}}

Se alguma informação não for aplicável ou identificável, use 'null' ou uma lista vazia para 'suggestions'.
"""

        try:
            response = await self.model.generate_content_async(prompt)
            cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```")
            structured_feedback = StructuredFeedback.model_validate_json(cleaned_text)
            
            # Store feedback in memory
            feedback_id = f"feedback_{datetime.now().timestamp()}"
            await self.memory.remember(feedback_id, structured_feedback.model_dump_json())
            logger.info(f"Feedback {feedback_id} coletado e armazenado.")

            return structured_feedback
        except json.JSONDecodeError as e:
            logger.error(f"Falha ao decodificar JSON da resposta do LLM para feedback: {e}\nResposta: {response.text}", exc_info=True)
            # Retorna um StructuredFeedback com erro para manter o tipo de retorno
            return StructuredFeedback(sentiment="neutro", accuracy_rating=None, suggestions=["Falha ao processar feedback"], relevant_query=context.query, relevant_agent=context.agent_type)
        except Exception as e:
            logger.error(f"Erro inesperado ao coletar feedback: {e}", exc_info=True)
            # Retorna um StructuredFeedback com erro para manter o tipo de retorno
            return StructuredFeedback(sentiment="neutro", accuracy_rating=None, suggestions=[f"Erro inesperado: {str(e)}"], relevant_query=context.query, relevant_agent=context.agent_type)

# Example usage (for testing purposes)
async def main():
    feedback_agent = FeedbackAgent()
    sample_context = FeedbackContext(query="qual a dose de vitamina C?", response_summary="A dose de vitamina C varia...", agent_type="RAG")
    sample_feedback = "A resposta foi boa, mas poderia ser mais detalhada sobre as fontes."
    
    structured_data = await feedback_agent.collect_feedback(sample_feedback, sample_context)
    logger.info(f"Feedback Estruturado: {structured_data}")

if __name__ == "__main__":
    import asyncio
    # from datetime import datetime # Import datetime here for example usage
    asyncio.run(main())