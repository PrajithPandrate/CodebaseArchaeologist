from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from typing import Optional
from datetime import datetime
import uuid


class Relationship(SQLModel, table=True):
    __tablename__ = "relationships"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repository_id: str = Field(foreign_key="repositories.id", index=True)
    source_type: str = Field(index=True)
    source_id: str = Field(index=True)
    target_type: str = Field(index=True)
    target_id: str = Field(index=True)
    relationship_type: str = Field(index=True)  # modified_by | introduced_in | discussed_in | fixes | references | reviewed_by | depends_on
    confidence: float = 1.0
    evidence: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
