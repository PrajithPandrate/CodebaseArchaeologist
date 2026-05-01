from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileRead(BaseModel):
    id: str
    repository_id: str
    path: str
    language: Optional[str] = None
    size_bytes: int
    line_count: int
    churn_score: float
    author_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str  # file | directory
    language: Optional[str] = None
    size_bytes: int = 0
    churn_score: float = 0.0
    children: Optional[list["FileTreeNode"]] = None

    model_config = {"from_attributes": True}


class FileHistoryRead(BaseModel):
    file_id: str
    file_path: str
    commits: list[dict] = []
    authors: list[dict] = []
    pull_requests: list[dict] = []
    issues: list[dict] = []
    timeline: list[dict] = []
    churn_score: float = 0.0
    first_seen: Optional[datetime] = None
    last_modified: Optional[datetime] = None
