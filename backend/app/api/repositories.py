from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import re

from ..database import get_session
from ..models import Repository, IngestionJob
from ..schemas.repository import RepositoryCreate, RepositoryRead, RepositoryListItem, IngestionJobRead, IngestionStatusRead
from ..services.hotspot_analysis import get_dashboard_stats

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extracts owner and repo name from GitHub URL."""
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    return match.group(1), match.group(2)


@router.post("", response_model=dict)
async def create_repository(
    body: RepositoryCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    owner, name = _parse_github_url(body.github_url)

    # Check if already exists
    existing = (await session.execute(
        select(Repository).where(
            Repository.owner == owner,
            Repository.name == name,
        )
    )).scalar_one_or_none()

    if existing and existing.status in ("ready", "ingesting"):
        raise HTTPException(
            status_code=409,
            detail=f"Repository {owner}/{name} is already indexed (status: {existing.status}). "
                   "Use POST /api/repositories/{id}/reindex to re-ingest."
        )

    # Sanitize token — never store full token
    token_hint = None
    if body.github_token:
        token_hint = f"...{body.github_token[-4:]}" if len(body.github_token) > 4 else "****"

    repo = Repository(
        owner=owner,
        name=name,
        github_url=body.github_url,
        status="pending",
        include_issues=body.include_issues,
        include_pr_comments=body.include_pr_comments,
        include_commit_diffs=body.include_commit_diffs,
        include_docs=body.include_docs,
        github_token_hint=token_hint,
    )
    session.add(repo)
    await session.flush()

    job = IngestionJob(
        repository_id=repo.id,
        status="queued",
        current_stage="queued",
        logs=[{"ts": datetime.utcnow().isoformat(), "stage": "queued", "msg": "Job queued"}],
    )
    session.add(job)
    await session.commit()

    # Enqueue background task
    from ..workers.tasks import ingest_repository
    ingest_repository.delay(repo.id, body.github_token)

    return {
        "repository_id": repo.id,
        "ingestion_job_id": job.id,
        "status": "queued",
    }


@router.get("", response_model=list[RepositoryListItem])
async def list_repositories(session: AsyncSession = Depends(get_session)):
    repos = (await session.execute(
        select(Repository).order_by(Repository.created_at.desc())
    )).scalars().all()
    return repos


@router.get("/{repo_id}", response_model=RepositoryRead)
async def get_repository(repo_id: str, session: AsyncSession = Depends(get_session)):
    repo = (await session.execute(
        select(Repository).where(Repository.id == repo_id)
    )).scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    stats = None
    if repo.status == "ready":
        stats = await get_dashboard_stats(session, repo_id)

    result = RepositoryRead.model_validate(repo)
    result.stats = stats
    return result


@router.get("/{repo_id}/ingestion/{job_id}", response_model=IngestionStatusRead)
async def get_ingestion_status(
    repo_id: str, job_id: str, session: AsyncSession = Depends(get_session)
):
    job = (await session.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.repository_id == repo_id,
        )
    )).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")

    repo = (await session.execute(
        select(Repository).where(Repository.id == repo_id)
    )).scalar_one_or_none()

    return IngestionStatusRead(
        job=IngestionJobRead.model_validate(job),
        repository=RepositoryListItem.model_validate(repo),
    )


@router.get("/{repo_id}/ingestion", response_model=IngestionJobRead)
async def get_latest_ingestion(repo_id: str, session: AsyncSession = Depends(get_session)):
    job = (await session.execute(
        select(IngestionJob)
        .where(IngestionJob.repository_id == repo_id)
        .order_by(IngestionJob.created_at.desc())
    )).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No ingestion job found")
    return job


@router.post("/{repo_id}/reindex", response_model=dict)
async def reindex_repository(
    repo_id: str,
    session: AsyncSession = Depends(get_session),
):
    repo = (await session.execute(
        select(Repository).where(Repository.id == repo_id)
    )).scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    job = IngestionJob(
        repository_id=repo_id,
        status="queued",
        current_stage="queued",
        logs=[{"ts": datetime.utcnow().isoformat(), "stage": "queued", "msg": "Re-index job queued"}],
    )
    repo.status = "pending"
    session.add(job)
    await session.commit()

    from ..workers.tasks import ingest_repository
    ingest_repository.delay(repo_id, None)

    return {"ingestion_job_id": job.id, "status": "queued"}


@router.delete("/{repo_id}", response_model=dict)
async def delete_repository(repo_id: str, session: AsyncSession = Depends(get_session)):
    repo = (await session.execute(
        select(Repository).where(Repository.id == repo_id)
    )).scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Cascade delete all related data
    import shutil
    import os
    if repo.local_path and os.path.exists(repo.local_path):
        shutil.rmtree(repo.local_path, ignore_errors=True)

    await session.delete(repo)
    await session.commit()
    return {"deleted": True, "repository_id": repo_id}
