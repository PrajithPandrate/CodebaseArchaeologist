from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from pgvector.sqlalchemy import Vector
from typing import Optional
from datetime import datetime
import uuid


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    source_type: str = ""  # issue | pull_request | review | commit
    source_id: Optional[str] = Field(default=None, index=True)
    author_login: str = ""
    body: str = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = None
    github_url: str = ""
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(1536)))
