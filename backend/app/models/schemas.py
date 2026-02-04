from pydantic import BaseModel, Field


class CaseRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=20000)


class LegalIssue(BaseModel):
    id: str
    label: str
    description: str
    relevant_facts: list[str]


class FactPattern(BaseModel):
    summary: str
    parties: list[str]
    issues: list[LegalIssue] = Field(default_factory=list, max_length=4)
    jurisdiction: str = "California"


class StatuteResult(BaseModel):
    code: str
    section: str
    title: str
    full_text: str
    url: str
    relevance_summary: str
    case_snippet: str
    confidence: float = Field(ge=0, le=1)
    source_issue_id: str


class CaseLawResult(BaseModel):
    case_name: str
    citation: str
    court: str
    date_filed: str
    url: str
    snippet: str
    relevance_summary: str
    related_statutes: list[str]
    confidence: float = Field(ge=0, le=1)
    source_issue_id: str


class FinalResult(BaseModel):
    run_id: str
    fact_pattern: FactPattern
    statutes: list[StatuteResult] = Field(default_factory=list)
    case_law: list[CaseLawResult] = Field(default_factory=list)


class CaseResponse(BaseModel):
    run_id: str
