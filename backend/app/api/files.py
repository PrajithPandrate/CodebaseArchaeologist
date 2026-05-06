from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..database import get_session
from ..models import File, CodeChunk, Commit, CommitFileChange, PullRequest, PullRequestCommit, Issue, Relationship
from ..schemas.file import FileRead, FileTreeNode, FileHistoryRead

router = APIRouter(prefix="/api/repositories/{repo_id}/files", tags=["files"])


def _build_tree(files: list[File]) -> list[FileTreeNode]:
    """Converts flat file list into nested tree structure."""
    root: dict = {}

    for f in files:
        parts = f.path.split("/")
        current = root
        for part in parts[:-1]:
            if part not in current:
                current[part] = {"__meta__": {"type": "directory", "path": "/".join(parts[:parts.index(part) + 1])}}
            current = current[part]
        current[parts[-1]] = f

    def _to_nodes(d: dict, prefix: str = "") -> list[FileTreeNode]:
        nodes = []
        for key, val in sorted(d.items()):
            if key == "__meta__":
                continue
            if isinstance(val, dict):
                meta = val.get("__meta__", {})
                children = _to_nodes(val, f"{prefix}{key}/")
                nodes.append(FileTreeNode(
                    name=key,
                    path=meta.get("path", f"{prefix}{key}"),
                    type="directory",
                    children=children,
                ))
            elif isinstance(val, File):
                nodes.append(FileTreeNode(
                    name=key,
                    path=val.path,
                    type="file",
                    language=val.language,
                    size_bytes=val.size_bytes,
                    churn_score=val.churn_score,
                ))
        return nodes

    return _to_nodes(root)


@router.get("", response_model=list[FileTreeNode])
async def get_file_tree(
    repo_id: str,
    session: AsyncSession = Depends(get_session),
):
    files = (await session.execute(
        select(File).where(File.repository_id == repo_id).order_by(File.path)
    )).scalars().all()
    return _build_tree(list(files))


@router.get("/{file_id}", response_model=FileRead)
async def get_file(
    repo_id: str,
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    file = (await session.execute(
        select(File).where(File.id == file_id, File.repository_id == repo_id)
    )).scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.get("/{file_id}/content")
async def get_file_content(
    repo_id: str,
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Returns file content by reading from git."""
    from ..models import Repository
    from ..services.git_history import GitHistoryService

    file = (await session.execute(
        select(File).where(File.id == file_id, File.repository_id == repo_id)
    )).scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    repo = (await session.execute(
        select(Repository).where(Repository.id == repo_id)
    )).scalar_one_or_none()

    if not repo or not repo.local_path:
        raise HTTPException(status_code=400, detail="Repository not ingested yet")

    try:
        git_svc = GitHistoryService(repo.local_path)
        content = git_svc.read_file(repo.default_branch, file.path)
        return {"path": file.path, "content": content or "", "language": file.language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/history", response_model=FileHistoryRead)
async def get_file_history(
    repo_id: str,
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    file = (await session.execute(
        select(File).where(File.id == file_id, File.repository_id == repo_id)
    )).scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Commits that touched this file
    changes = (await session.execute(
        select(CommitFileChange, Commit)
        .join(Commit, Commit.id == CommitFileChange.commit_id)
        .where(CommitFileChange.file_id == file_id)
        .order_by(Commit.committed_at.desc())
        .limit(50)
    )).all()

    commits_data = []
    commit_ids = set()
    for change, commit in changes:
        commit_ids.add(commit.id)
        commits_data.append({
            "sha": commit.sha,
            "message": commit.message.splitlines()[0][:100],
            "author": commit.author_name,
            "date": commit.committed_at.isoformat() if commit.committed_at else None,
            "github_url": commit.github_url,
            "status": change.status,
            "additions": change.additions,
            "deletions": change.deletions,
        })

    # Authors
    from collections import Counter
    author_counts: Counter = Counter()
    for change, commit in changes:
        author_counts[commit.author_name] += 1

    authors = [{"name": name, "commits": count} for name, count in author_counts.most_common()]

    # PRs via relationships
    pr_rels = (await session.execute(
        select(Relationship).where(
            Relationship.repository_id == repo_id,
            Relationship.source_type == "pull_request",
            Relationship.target_type == "commit",
            Relationship.target_id.in_(list(commit_ids)),
        ).limit(20)
    )).scalars().all()

    pr_ids = {r.source_id for r in pr_rels}
    prs_data = []
    if pr_ids:
        prs = (await session.execute(
            select(PullRequest).where(PullRequest.id.in_(list(pr_ids)))
        )).scalars().all()
        prs_data = [
            {
                "number": pr.github_pr_number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.author_login,
                "merged": pr.merged,
                "date": pr.created_at.isoformat() if pr.created_at else None,
                "github_url": pr.github_url,
            }
            for pr in prs
        ]

    first_seen = min((c.committed_at for _, c in changes if c.committed_at), default=None)
    last_modified = max((c.committed_at for _, c in changes if c.committed_at), default=None)

    return FileHistoryRead(
        file_id=file_id,
        file_path=file.path,
        commits=commits_data,
        authors=authors,
        pull_requests=prs_data,
        issues=[],
        timeline=[],
        churn_score=file.churn_score,
        first_seen=first_seen,
        last_modified=last_modified,
    )
