from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text
from pgvector.sqlalchemy import Vector
from typing import Optional
from datetime import datetime
import uuid


class Issue(SQLModel, table=True):
    __tablename__ = "issues"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    github_issue_number: int = Field(index=True)
    title: str = Field(sa_column=Column(Text))
    body: Optional[str] = Field(default=None, sa_column=Column(Text))
    state: str = "open"
    author_login: str = ""
    labels: Optional[list] = Field(default=None, sa_column=Column(JSON))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    github_url: str = ""
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(1536)))
