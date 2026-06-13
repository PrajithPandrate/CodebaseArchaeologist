from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AskContext(BaseModel):
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    selected_text: Optional[str] = None
    symbol_name: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    context: Optional[AskContext] = None


class EvidenceItem(BaseModel):
    id: str
    source_id: Optional[str] = None  # internal DB id of the source record
    citation_label: str
    source_type: str  # commit | pr | issue | comment | code | doc
    title: str
    snippet: str
    author: Optional[str] = None
    date: Optional[datetime] = None
    github_url: Optional[str] = None
    relevance_score: float
    why_selected: Optional[str] = None


class TimelineItem(BaseModel):
    date: Optional[datetime] = None
    event_type: str  # commit | pr_created | pr_merged | issue_opened | issue_closed | comment | refactor
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    citation_id: Optional[str] = None
    github_url: Optional[str] = None


class KnownInferred(BaseModel):
    known: list[str] = []
    inferred: list[str] = []
    unknown: list[str] = []


class AskResponse(BaseModel):
    question_id: str
    answer: str
    confidence: float
    confidence_explanation: str
    timeline: list[TimelineItem] = []
    evidence: list[EvidenceItem] = []
    known_vs_inferred: KnownInferred
    related_files: list[str] = []
    follow_up_questions: list[str] = []
