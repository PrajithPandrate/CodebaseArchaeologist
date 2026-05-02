from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from pgvector.sqlalchemy import Vector
from typing import Optional
from datetime import datetime
import uuid


class CodeChunk(SQLModel, table=True):
    __tablename__ = "code_chunks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    file_id: str = Field(foreign_key="files.id", index=True)
    symbol_name: Optional[str] = Field(default=None, index=True)
    symbol_type: Optional[str] = None  # function | class | method | file_section
    start_line: int = 0
    end_line: int = 0
    content: str = Field(sa_column=Column(Text))
    content_hash: Optional[str] = None
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(1536)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
