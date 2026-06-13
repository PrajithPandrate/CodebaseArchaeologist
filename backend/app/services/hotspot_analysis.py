"""
Computes hotspot metrics: file churn, author concentration, risk scores.
"""
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import File, Commit, CommitFileChange, PullRequest, Issue, Relationship


async def get_dashboard_stats(session: AsyncSession, repo_id: str) -> dict:
    file_count = (await session.execute(
        select(func.count(File.id)).where(File.repository_id == repo_id)
    )).scalar() or 0

    commit_count = (await session.execute(
        select(func.count(Commit.id)).where(Commit.repository_id == repo_id)
    )).scalar() or 0

    pr_count = (await session.execute(
        select(func.count(PullRequest.id)).where(PullRequest.repository_id == repo_id)
    )).scalar() or 0

    issue_count = (await session.execute(
        select(func.count(Issue.id)).where(Issue.repository_id == repo_id)
    )).scalar() or 0

    # Unique authors
    author_count = (await session.execute(
        select(func.count(func.distinct(Commit.author_email)))
        .where(Commit.repository_id == repo_id)
    )).scalar() or 0

    # Oldest commit
    oldest = (await session.execute(
        select(func.min(Commit.committed_at)).where(Commit.repository_id == repo_id)
    )).scalar()

    # Top files by churn
    top_churn = (await session.execute(
        select(File.path, File.churn_score, File.author_count)
        .where(File.repository_id == repo_id)
        .order_by(File.churn_score.desc())
        .limit(10)
    )).all()

    # Top authors by commits
    top_authors = (await session.execute(
        select(Commit.author_name, func.count(Commit.id).label("commit_count"))
        .where(Commit.repository_id == repo_id)
        .group_by(Commit.author_name)
        .order_by(func.count(Commit.id).desc())
        .limit(10)
    )).all()

    # Commits over time (monthly)
    commits_over_time = (await session.execute(
        text("""
            SELECT DATE_TRUNC('month', committed_at) as month, COUNT(*) as count
            FROM commits
            WHERE repository_id = :repo_id AND committed_at IS NOT NULL
            GROUP BY month
            ORDER BY month
            LIMIT 24
        """),
        {"repo_id": repo_id},
    )).fetchall()

    return {
        "total_files": file_count,
        "total_commits": commit_count,
        "total_prs": pr_count,
        "total_issues": issue_count,
        "total_authors": author_count,
        "oldest_commit": oldest.isoformat() if oldest else None,
        "top_churn_files": [
            {"path": r[0], "churn_score": r[1], "author_count": r[2]}
            for r in top_churn
        ],
        "top_authors": [
            {"name": r[0], "commit_count": r[1]}
            for r in top_authors
        ],
        "commits_over_time": [
            {"month": r[0].isoformat() if r[0] else None, "count": r[1]}
            for r in commits_over_time
        ],
    }


async def get_hotspots(session: AsyncSession, repo_id: str) -> list[dict]:
    """Returns files ranked by risk = churn + author_count normalization."""
    files = (await session.execute(
        select(File)
        .where(File.repository_id == repo_id, File.churn_score > 0)
        .order_by(File.churn_score.desc())
        .limit(50)
    )).scalars().all()

    if not files:
        return []

    max_churn = max(f.churn_score for f in files) or 1
    max_authors = max(f.author_count for f in files) or 1

    hotspots = []
    for f in files:
        churn_norm = f.churn_score / max_churn
        author_norm = f.author_count / max_authors
        risk = 0.6 * churn_norm + 0.4 * author_norm
        hotspots.append({
            "path": f.path,
            "language": f.language,
            "churn_score": f.churn_score,
            "author_count": f.author_count,
            "risk_score": round(risk, 3),
            "line_count": f.line_count,
        })

    return sorted(hotspots, key=lambda x: x["risk_score"], reverse=True)
