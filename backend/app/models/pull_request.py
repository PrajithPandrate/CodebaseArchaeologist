from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from pgvector.sqlalchemy import Vector
from typing import Optional
from datetime import datetime
import uuid


class PullRequest(SQLModel, table=True):
    __tablename__ = "pull_requests"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    github_pr_number: int = Field(index=True)
    title: str = Field(sa_column=Column(Text))
    body: Optional[str] = Field(default=None, sa_column=Column(Text))
    state: str = "open"  # open | closed | merged
    author_login: str = ""
    merged: bool = False
    merged_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    github_url: str = ""
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column("pr_embedding", Vector(1536)))


class PullRequestCommit(SQLModel, table=True):
    __tablename__ = "pull_request_commits"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    pull_request_id: str = Field(foreign_key="pull_requests.id", index=True)
    commit_id: str = Field(foreign_key="commits.id", index=True)
