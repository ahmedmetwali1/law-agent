from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Fact(BaseModel):
    """
    Represents a specific legal or material fact in the case.
    """
    content: str = Field(..., description="The fact description")
    source: str = Field(..., description="Where this fact came from (e.g., User statement, Document X)")
    status: Literal["confirmed", "disputed", "assumed"] = "assumed"

class Evidence(BaseModel):
    """
    Represents a piece of evidence supporting a fact.
    """
    description: str = Field(..., description="Description of the evidence")
    type: str = Field(..., description="Type of evidence (e.g., document, testimony)")
    relevance: Optional[str] = Field(None, description="Why is this relevant?")

class Party(BaseModel):
    """
    Represents a party in the legal matter.
    """
    name: str = Field(..., description="Name or role (e.g., Client, Opponent)")
    role: Literal["plaintiff", "defendant", "witness", "other"]
    description: Optional[str] = None

class CaseStateModel(BaseModel):
    """
    Structured representation of the case gathered by the Investigator.
    """
    summary: str = Field(..., description="Brief summary of the case")
    facts: List[Fact] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    parties: List[Party] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list, description="Critical information still needed")
    classification: Optional[str] = Field(None, description="Legal classification (e.g., Civil, Criminal, Commercial)")
