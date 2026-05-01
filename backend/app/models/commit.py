from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from typing import Optional
from datetime import datetime
import uuid


class Commit(SQLModel, table=True):
    __tablename__ = "commits"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    sha: str = Field(index=True)
    message: str = Field(sa_column=Column(Text))
    author_name: str = ""
    author_email: str = ""
    committed_at: Optional[datetime] = None
    github_url: Optional[str] = None


class CommitFileChange(SQLModel, table=True):
    __tablename__ = "commit_file_changes"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    commit_id: str = Field(foreign_key="commits.id", index=True)
    file_id: Optional[str] = Field(default=None, foreign_key="files.id")
    file_path: str = Field(index=True)
    status: str = "modified"  # added | modified | deleted | renamed
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = Field(default=None, sa_column=Column(Text))
