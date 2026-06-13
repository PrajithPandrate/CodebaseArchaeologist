from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from pgvector.sqlalchemy import Vector
from typing import Optional
from datetime import datetime
import uuid


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    path: str = ""
    title: str = ""
    content: str = Field(sa_column=Column(Text))
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(1536)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
