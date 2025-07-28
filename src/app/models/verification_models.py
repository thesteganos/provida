from pydantic import BaseModel, Field
from typing import List, Optional

class Claim(BaseModel):
    subject: str
    predicate: str
    object: str

class VerificationReport(BaseModel):
    hallucination_detected: bool
    verified_count: int
    unverified_count: int
    verified_claims: List[Claim]
    unverified_claims: List[Claim]
    message: Optional[str] = None
