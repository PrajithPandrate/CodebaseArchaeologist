from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text
from typing import Optional
from datetime import datetime
import uuid


class Repository(SQLModel, table=True):
    __tablename__ = "repositories"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    owner: str
    name: str
    github_url: str
    default_branch: str = "main"
    local_path: Optional[str] = None
    status: str = "pending"  # pending | ingesting | ready | failed
    include_issues: bool = True
    include_pr_comments: bool = True
    include_commit_diffs: bool = True
    include_docs: bool = True
    github_token_hint: Optional[str] = None  # last 4 chars only, never full token
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IngestionJob(SQLModel, table=True):
    __tablename__ = "ingestion_jobs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    status: str = "queued"  # queued | running | completed | failed
    current_stage: str = ""
    progress_percent: int = 0
    logs: Optional[list] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
