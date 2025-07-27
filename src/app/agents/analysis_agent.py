from app.core.llm_provider import llm_provider
from app.config.settings import settings
from typing import Dict, Any

class AnalysisAgent:
    def __init__(self):
        self.model = llm_provider.get_model(settings["models"]["analysis_agent"])

    def classify_evidence(self, text: str) -> Dict[str, Any]:
        """Classifies the provided text by evidence level (A, B, C, D, E).

        Args:
            text (str): The text to classify.

        Returns:
            Dict[str, Any]: A dictionary containing the classified evidence level and justification.
        """
        prompt = f"""Você é um Agente de Análise e Classificação. Sua tarefa é avaliar o texto fornecido e classificá-lo de acordo com os níveis de evidência (A, B, C, D, E). Além da classificação, forneça uma breve justificativa para a sua escolha.

        Níveis de Evidência:
        A: Evidência forte (ex: meta-análises de ensaios clínicos randomizados, revisões sistemáticas).
        B: Evidência moderada (ex: ensaios clínicos randomizados individuais, estudos de coorte bem delineados).
        C: Evidência limitada (ex: estudos caso-controle, séries de casos, estudos observacionais).
        D: Opinião de especialista ou consenso (ex: diretrizes baseadas em consenso, opinião de comitês de especialistas).
        E: Evidência anedótica ou sem suporte científico direto.

        Texto para Classificação: {text}

        Formato de Saída (JSON):
        {{
            "evidence_level": "Nível de evidência (A, B, C, D, E)",
            "justification": "Justificativa para a classificação"
        }}

        Certifique-se de que a saída seja um JSON válido e completo.
        """

        try:
            response = self.model.generate_content(prompt)
            import json
            classification_data = json.loads(response.text)
            return classification_data
        except Exception as e:
            print(f"Error classifying evidence: {e}")
            return {"error": str(e), "evidence_level": "E", "justification": "Failed to classify."}
