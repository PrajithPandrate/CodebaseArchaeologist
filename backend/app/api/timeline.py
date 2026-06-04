from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime

from ..database import get_session
from ..models import Commit, CommitFileChange, PullRequest, Issue, Comment, File, PullRequestCommit, Relationship

router = APIRouter(prefix="/api/repositories/{repo_id}/timeline", tags=["timeline"])


@router.get("")
async def get_timeline(
    repo_id: str,
    file_path: Optional[str] = Query(None),
    symbol_name: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    events = []

    # Parse date filters
    start = None
    end = None
    try:
        if start_date:
            start = datetime.fromisoformat(start_date)
        if end_date:
            end = datetime.fromisoformat(end_date)
    except Exception:
        pass

    # Get relevant commit IDs if file_path given
    commit_ids = None
    if file_path:
        file_row = (await session.execute(
            select(File).where(File.repository_id == repo_id, File.path == file_path)
        )).scalar_one_or_none()
        if file_row:
            changes = (await session.execute(
                select(CommitFileChange.commit_id)
                .where(
                    CommitFileChange.repository_id == repo_id,
                    CommitFileChange.file_id == file_row.id,
                )
            )).scalars().all()
            commit_ids = set(changes)

    # Commits
    commit_query = select(Commit).where(Commit.repository_id == repo_id)
    if commit_ids is not None:
        commit_query = commit_query.where(Commit.id.in_(list(commit_ids)))
    if keyword:
        commit_query = commit_query.where(Commit.message.ilike(f"%{keyword}%"))
    if start:
        commit_query = commit_query.where(Commit.committed_at >= start)
    if end:
        commit_query = commit_query.where(Commit.committed_at <= end)
    commit_query = commit_query.order_by(Commit.committed_at.desc()).limit(50)

    commits = (await session.execute(commit_query)).scalars().all()
    for c in commits:
        events.append({
            "id": c.id,
            "date": c.committed_at.isoformat() if c.committed_at else None,
            "event_type": "commit",
            "title": c.message.splitlines()[0][:100],
            "description": c.message[:300],
            "author": c.author_name,
            "github_url": c.github_url,
        })

    # PRs
    pr_query = select(PullRequest).where(PullRequest.repository_id == repo_id)
    if keyword:
        pr_query = pr_query.where(PullRequest.title.ilike(f"%{keyword}%"))
    if start:
        pr_query = pr_query.where(PullRequest.created_at >= start)
    if end:
        pr_query = pr_query.where(PullRequest.created_at <= end)
    pr_query = pr_query.order_by(PullRequest.created_at.desc()).limit(30)

    prs = (await session.execute(pr_query)).scalars().all()
    for pr in prs:
        events.append({
            "id": pr.id,
            "date": pr.created_at.isoformat() if pr.created_at else None,
            "event_type": "pr_created",
            "title": pr.title,
            "description": (pr.body or "")[:200],
            "author": pr.author_login,
            "github_url": pr.github_url,
            "merged": pr.merged,
        })
        if pr.merged and pr.merged_at:
            events.append({
                "id": f"{pr.id}_merged",
                "date": pr.merged_at.isoformat(),
                "event_type": "pr_merged",
                "title": f"Merged: {pr.title}",
                "author": pr.author_login,
                "github_url": pr.github_url,
            })

    # Issues
    issue_query = select(Issue).where(Issue.repository_id == repo_id)
    if keyword:
        issue_query = issue_query.where(Issue.title.ilike(f"%{keyword}%"))
    if start:
        issue_query = issue_query.where(Issue.created_at >= start)
    if end:
        issue_query = issue_query.where(Issue.created_at <= end)
    issue_query = issue_query.order_by(Issue.created_at.desc()).limit(30)

    issues = (await session.execute(issue_query)).scalars().all()
    for issue in issues:
        events.append({
            "id": issue.id,
            "date": issue.created_at.isoformat() if issue.created_at else None,
            "event_type": "issue_opened",
            "title": issue.title,
            "description": (issue.body or "")[:200],
            "author": issue.author_login,
            "github_url": issue.github_url,
            "state": issue.state,
            "labels": issue.labels or [],
        })
        if issue.closed_at:
            events.append({
                "id": f"{issue.id}_closed",
                "date": issue.closed_at.isoformat(),
                "event_type": "issue_closed",
                "title": f"Closed: {issue.title}",
                "author": issue.author_login,
                "github_url": issue.github_url,
            })

    # Sort by date
    def _sort_key(e):
        d = e.get("date")
        if not d:
            return ""
        return d

    events.sort(key=_sort_key, reverse=True)
    return {"events": events, "total": len(events)}
