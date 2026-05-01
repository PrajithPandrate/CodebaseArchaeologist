from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class File(SQLModel, table=True):
    __tablename__ = "files"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    path: str
    language: Optional[str] = None
    size_bytes: int = 0
    current_hash: Optional[str] = None
    line_count: int = 0
    churn_score: float = 0.0  # total additions + deletions over history
    author_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
