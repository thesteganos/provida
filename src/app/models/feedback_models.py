from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class FeedbackContext(BaseModel):
    query: str
    response_summary: str
    agent_type: str

class StructuredFeedback(BaseModel):
    sentiment: Literal["positivo", "negativo", "neutro"] = Field(description="Sentimento geral do feedback.")
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5, description="Avaliação da precisão da resposta (escala de 1 a 5).")
    suggestions: List[str] = Field(default_factory=list, description="Sugestões de melhoria ou novas funcionalidades.")
    relevant_query: Optional[str] = Field(None, description="A query original à qual o feedback se refere.")
    relevant_agent: Optional[str] = Field(None, description="O agente principal ao qual o feedback se refere.")
