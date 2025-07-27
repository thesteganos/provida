import unittest
import os
import asyncio
from unittest.mock import patch, MagicMock

class TestDeepResearchOrchestrator(unittest.TestCase):

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch('pro_vida.orchestrator.ResearchAgent')
    def test_run_isolates_state(self, MockResearchAgent):
        from src.pro_vida.orchestrator import DeepResearchOrchestrator
        # Crie uma instância mock do ResearchAgent
        mock_agent_instance = MockResearchAgent.return_value

        # Configure o mock para retornar resultados de pesquisa diferentes para diferentes tópicos
        async def mock_search_web(topic):
            if topic == "topic1":
                return [{"result": "topic1_result"}]
            elif topic == "topic2":
                return [{"result": "topic2_result"}]
            return []

        mock_agent_instance.search_web = MagicMock(side_effect=mock_search_web)

        # Crie o orquestrador
        orchestrator = DeepResearchOrchestrator()
        loop = asyncio.new_event_loop()

        # Execute o orquestrador com o primeiro tópico
        results1 = orchestrator.run("topic1", loop)

        # Execute o orquestrador com o segundo tópico
        results2 = orchestrator.run("topic2", loop)

        loop.close()

        # Verifique se os resultados são os esperados e não são combinados
        self.assertEqual(results1, [{"result": "topic1_result"}])
        self.assertEqual(results2, [{"result": "topic2_result"}])

if __name__ == '__main__':
    unittest.main()
