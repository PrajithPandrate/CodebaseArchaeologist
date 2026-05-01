from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text
from typing import Optional
from datetime import datetime
import uuid


class Question(SQLModel, table=True):
    __tablename__ = "questions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    question_text: str = Field(sa_column=Column(Text))
    answer_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    confidence: float = 0.0
    context: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    timeline: Optional[list] = Field(default=None, sa_column=Column(JSON))
    related_files: Optional[list] = Field(default=None, sa_column=Column(JSON))
    follow_up_questions: Optional[list] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnswerEvidence(SQLModel, table=True):
    __tablename__ = "answer_evidence"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    question_id: str = Field(foreign_key="questions.id", index=True)
    source_type: str = ""
    source_id: str = ""
    snippet: str = Field(sa_column=Column(Text))
    relevance_score: float = 0.0
    citation_label: str = ""
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[datetime] = None
    github_url: Optional[str] = None
