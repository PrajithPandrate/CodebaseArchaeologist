from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
from datetime import datetime


class RepositoryCreate(BaseModel):
    github_url: str
    github_token: Optional[str] = None
    include_issues: bool = True
    include_pr_comments: bool = True
    include_commit_diffs: bool = True
    include_docs: bool = True

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        if "github.com" not in v:
            raise ValueError("URL must be a GitHub repository URL")
        return v.rstrip("/")


class RepositoryRead(BaseModel):
    id: str
    owner: str
    name: str
    github_url: str
    default_branch: str
    status: str
    created_at: datetime
    updated_at: datetime
    stats: Optional[dict] = None

    model_config = {"from_attributes": True}


class RepositoryListItem(BaseModel):
    id: str
    owner: str
    name: str
    github_url: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestionJobRead(BaseModel):
    id: str
    repository_id: str
    status: str
    current_stage: str
    progress_percent: int
    logs: Optional[list] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngestionStatusRead(BaseModel):
    job: IngestionJobRead
    repository: RepositoryListItem
