"""
Research Agent that uses Brave Search and can invoke Email Agent.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# from pydantic_ai import Agent, RunContext # Removido temporariamente

from pro_vida.core.llm_provider import get_model_for_agent
from pro_vida.tools.web_search import search_web_tool

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert research assistant with the ability to search the web and create email drafts. Your primary goal is to help users find relevant information and communicate findings effectively.

Your capabilities:
1. **Web Search**: Use Brave Search to find current, relevant information on any topic
2. **Email Creation**: Create professional email drafts through Gmail when requested

When conducting research:
- Use specific, targeted search queries
- Analyze search results for relevance and credibility
- Synthesize information from multiple sources
- Provide clear, well-organized summaries
- Include source URLs for reference

When creating emails:
- Use research findings to create informed, professional content
- Adapt tone and detail level to the intended recipient
- Include relevant sources and citations when appropriate
- Ensure emails are clear, concise, and actionable

Always strive to provide accurate, helpful, and actionable information.
"""


import os
from pro_vida.config.settings import settings

class ResearchAgent:
    def __init__(self):
        self.llm = get_model_for_agent('analysis_agent')
        # A chave da API de pesquisa será obtida de forma segura
        self.search_api_key = os.getenv("BRAVE_API_KEY")
        if not self.search_api_key:
            logger.warning("BRAVE_API_KEY não está definida. A pesquisa na web falhará.")

    async def search_web(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Pesquisa na web usando a API Brave Search.
        """
        if not self.search_api_key:
            return [{"error": "A chave da API de pesquisa não está configurada."}]

        try:
            max_results = min(max(max_results, 1), 20)

            results = await search_web_tool(
                api_key=self.search_api_key,
                query=query,
                count=max_results
            )

            logger.info(f"Encontrados {len(results)} resultados para a consulta: {query}")
            return results

        except Exception as e:
            logger.error(f"A pesquisa na web falhou: {e}")
            return [{"error": f"A pesquisa falhou: {str(e)}"}]