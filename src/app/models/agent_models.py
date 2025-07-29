from typing import List
from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """
    Modelo de dados para o resultado estruturado da análise de um texto.
    """
    summary: str = Field(..., description="Resumo conciso do texto.")
    evidence_level: str = Field(..., description="Nível de evidência classificado (A, B, C, D, E).")
    justification: str = Field(..., description="Justificativa para a classificação do nível de evidência.")
    keywords: List[str] = Field(default_factory=list, description="Lista de palavras-chave relevantes.")