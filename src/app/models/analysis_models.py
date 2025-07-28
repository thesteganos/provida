from pydantic import BaseModel, Field
from typing import List, Literal

class AnalysisResult(BaseModel):
    summary: str = Field(description="Um resumo conciso do texto, focado nos principais achados e conclusões.")
    evidence_level: Literal["A", "B", "C", "D", "E"] = Field(description="A letra correspondente ao nível de evidência (A, B, C, D, ou E).")
    justification: str = Field(description="Justificativa para a classificação do nível de evidência.")
    keywords: List[str] = Field(default_factory=list, description="Lista de palavras-chave relevantes extraídas do texto.")
