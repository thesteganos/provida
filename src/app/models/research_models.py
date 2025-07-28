from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CollectedDataItem(BaseModel):
    source_identifier: str
    content: str
    # Add other fields as needed, e.g., url, title, etc.

class AnalyzedDataItem(BaseModel):
    source_identifier: str
    analysis: Dict[str, Any] # This will likely be AnalysisResult from analysis_models.py

class FinalReport(BaseModel):
    summary: str
    citations_used: List[Dict[str, Any]] # This will likely be a list of Citation objects

class VerificationReport(BaseModel):
    hallucination_detected: bool
    verified_count: int
    unverified_count: int
    verified_claims: List[Dict[str, Any]] # This will likely be a list of Claim objects
    unverified_claims: List[Dict[str, Any]] # This will likely be a list of Claim objects
    message: Optional[str] = None
