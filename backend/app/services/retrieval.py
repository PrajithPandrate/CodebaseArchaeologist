"""
Hybrid retrieval: semantic search + keyword + graph expansion, with re-ranking.
"""
from typing import Optional
from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import (
    CodeChunk, PullRequest, Issue, Comment, Commit, CommitFileChange,
    File, Relationship, Document
)
from ..services.embeddings import embed_text
from ..schemas.ask import EvidenceItem
import uuid
from datetime import datetime

SOURCE_QUALITY = {
    "pull_request": 1.0,
    "pr": 1.0,
    "issue": 0.9,
    "commit": 0.75,
    "comment": 0.7,
    "code": 0.65,
    "doc": 0.6,
}


async def retrieve_evidence(
    session: AsyncSession,
    repo_id: str,
    question: str,
    context_file_path: Optional[str] = None,
    context_symbol: Optional[str] = None,
    top_k: int = 12,
) -> list[EvidenceItem]:
    """
    Performs hybrid retrieval and returns ranked evidence items.
    """
    # 1. Embed the question
    query_embedding = await embed_text(question)

    # 2. Semantic + keyword search across sources
    candidates = []

    candidates += await _search_code_chunks(session, repo_id, question, query_embedding, context_file_path)
    candidates += await _search_prs(session, repo_id, question, query_embedding)
    candidates += await _search_issues(session, repo_id, question, query_embedding)
    candidates += await _search_comments(session, repo_id, question, query_embedding)
    candidates += await _search_commits(session, repo_id, question)

    # 3. Graph expansion if file context provided
    if context_file_path:
        candidates += await _graph_expand(session, repo_id, context_file_path)

    # 4. Deduplicate by source_id
    seen = set()
    unique = []
    for c in candidates:
        key = (c["source_type"], c["source_id"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # 5. Re-rank
    ranked = _rerank(unique, question, context_file_path)

    # 6. Convert to EvidenceItem
    evidence = []
    for i, item in enumerate(ranked[:top_k]):
        label = f"[{i + 1}]"
        evidence.append(EvidenceItem(
            id=str(uuid.uuid4()),
            source_id=item.get("source_id"),
            citation_label=label,
            source_type=item["source_type"],
            title=item.get("title", ""),
            snippet=item.get("snippet", "")[:600],
            author=item.get("author"),
            date=item.get("date"),
            github_url=item.get("github_url"),
            relevance_score=round(item.get("final_score", 0.5), 3),
            why_selected=item.get("why_selected"),
        ))

    return evidence


async def _search_code_chunks(session, repo_id, question, embedding, file_path=None):
    results = []
    query = select(CodeChunk, File.path).join(File, File.id == CodeChunk.file_id).where(
        CodeChunk.repository_id == repo_id
    )
    if file_path:
        query = query.where(File.path == file_path)

    if embedding:
        # pgvector cosine similarity
        raw = await session.execute(
            text("""
                SELECT cc.id, cc.content, cc.symbol_name, cc.symbol_type,
                       cc.start_line, cc.end_line, f.path,
                       1 - (cc.embedding <=> CAST(:emb AS vector)) as similarity
                FROM code_chunks cc
                JOIN files f ON f.id = cc.file_id
                WHERE cc.repository_id = :repo_id
                  AND cc.embedding IS NOT NULL
                ORDER BY cc.embedding <=> CAST(:emb AS vector)
                LIMIT 20
            """),
            {"repo_id": repo_id, "emb": str(embedding)},
        )
        for row in raw.fetchall():
            results.append({
                "source_type": "code",
                "source_id": row[0],
                "title": f"{row[6]}:{row[4]}-{row[5]} ({row[2] or 'section'})",
                "snippet": row[1][:500],
                "semantic_score": float(row[7]),
                "file_path": row[6],
                "why_selected": "Semantic similarity to question",
            })
    else:
        # Keyword fallback
        words = question.lower().split()[:5]
        for chunk_row in (await session.execute(query.limit(50))).all():
            chunk = chunk_row[0]
            content_lower = chunk.content.lower()
            hits = sum(1 for w in words if w in content_lower)
            if hits > 1:
                results.append({
                    "source_type": "code",
                    "source_id": chunk.id,
                    "title": f"{chunk_row[1]}:{chunk.start_line}-{chunk.end_line}",
                    "snippet": chunk.content[:500],
                    "keyword_score": hits / len(words),
                    "file_path": chunk_row[1],
                    "why_selected": "Keyword match in code",
                })

    return results


async def _search_prs(session, repo_id, question, embedding):
    results = []
    if embedding:
        raw = await session.execute(
            text("""
                SELECT id, title, body, author_login, created_at, github_url, merged,
                       1 - (pr_embedding <=> CAST(:emb AS vector)) as similarity
                FROM pull_requests
                WHERE repository_id = :repo_id AND pr_embedding IS NOT NULL
                ORDER BY pr_embedding <=> CAST(:emb AS vector)
                LIMIT 10
            """),
            {"repo_id": repo_id, "emb": str(embedding)},
        )
        for row in raw.fetchall():
            results.append({
                "source_type": "pull_request",
                "source_id": row[0],
                "title": row[1],
                "snippet": (row[2] or "")[:400],
                "author": row[3],
                "date": row[4],
                "github_url": row[5],
                "semantic_score": float(row[7]),
                "why_selected": "PR semantically similar to question",
            })
    else:
        prs = (await session.execute(
            select(PullRequest).where(PullRequest.repository_id == repo_id).limit(50)
        )).scalars().all()
        words = question.lower().split()[:5]
        for pr in prs:
            text_blob = f"{pr.title or ''} {pr.body or ''}".lower()
            hits = sum(1 for w in words if w in text_blob)
            if hits >= 2:
                results.append({
                    "source_type": "pull_request",
                    "source_id": pr.id,
                    "title": pr.title,
                    "snippet": (pr.body or "")[:400],
                    "author": pr.author_login,
                    "date": pr.created_at,
                    "github_url": pr.github_url,
                    "keyword_score": hits / len(words),
                    "why_selected": "Keyword match in PR",
                })
    return results


async def _search_issues(session, repo_id, question, embedding):
    results = []
    if embedding:
        raw = await session.execute(
            text("""
                SELECT id, title, body, author_login, created_at, github_url,
                       1 - (embedding <=> CAST(:emb AS vector)) as similarity
                FROM issues
                WHERE repository_id = :repo_id AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT 10
            """),
            {"repo_id": repo_id, "emb": str(embedding)},
        )
        for row in raw.fetchall():
            results.append({
                "source_type": "issue",
                "source_id": row[0],
                "title": row[1],
                "snippet": (row[2] or "")[:400],
                "author": row[3],
                "date": row[4],
                "github_url": row[5],
                "semantic_score": float(row[6]),
                "why_selected": "Issue semantically similar to question",
            })
    else:
        issues = (await session.execute(
            select(Issue).where(Issue.repository_id == repo_id).limit(50)
        )).scalars().all()
        words = question.lower().split()[:5]
        for issue in issues:
            text_blob = f"{issue.title or ''} {issue.body or ''}".lower()
            hits = sum(1 for w in words if w in text_blob)
            if hits >= 2:
                results.append({
                    "source_type": "issue",
                    "source_id": issue.id,
                    "title": issue.title,
                    "snippet": (issue.body or "")[:400],
                    "author": issue.author_login,
                    "date": issue.created_at,
                    "github_url": issue.github_url,
                    "keyword_score": hits / len(words),
                    "why_selected": "Keyword match in issue",
                })
    return results


async def _search_comments(session, repo_id, question, embedding):
    results = []
    if embedding:
        raw = await session.execute(
            text("""
                SELECT id, body, author_login, created_at, github_url, source_type,
                       1 - (embedding <=> CAST(:emb AS vector)) as similarity
                FROM comments
                WHERE repository_id = :repo_id AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT 8
            """),
            {"repo_id": repo_id, "emb": str(embedding)},
        )
        for row in raw.fetchall():
            results.append({
                "source_type": "comment",
                "source_id": row[0],
                "title": f"Comment by {row[2]} ({row[5]})",
                "snippet": (row[1] or "")[:400],
                "author": row[2],
                "date": row[3],
                "github_url": row[4],
                "semantic_score": float(row[6]),
                "why_selected": "Comment semantically similar to question",
            })
    return results


async def _search_commits(session, repo_id, question):
    """Keyword search on commit messages."""
    words = [w for w in question.lower().split() if len(w) > 3][:6]
    if not words:
        return []

    commits = (await session.execute(
        select(Commit).where(Commit.repository_id == repo_id).limit(200)
    )).scalars().all()

    results = []
    for commit in commits:
        msg_lower = (commit.message or "").lower()
        hits = sum(1 for w in words if w in msg_lower)
        if hits >= 2:
            results.append({
                "source_type": "commit",
                "source_id": commit.id,
                "title": commit.message.splitlines()[0][:100],
                "snippet": commit.message[:400],
                "author": commit.author_name,
                "date": commit.committed_at,
                "github_url": commit.github_url,
                "keyword_score": hits / len(words),
                "why_selected": "Keyword match in commit message",
            })
    return sorted(results, key=lambda x: x["keyword_score"], reverse=True)[:10]


async def _graph_expand(session, repo_id, file_path):
    """Finds PRs/commits/issues related to a file via graph relationships."""
    # Get file id
    file_row = (await session.execute(
        select(File).where(File.repository_id == repo_id, File.path == file_path)
    )).scalar_one_or_none()

    if not file_row:
        return []

    # Commits that modified this file
    changes = (await session.execute(
        select(CommitFileChange).where(
            CommitFileChange.repository_id == repo_id,
            CommitFileChange.file_id == file_row.id,
        ).limit(20)
    )).scalars().all()

    commit_ids = {c.commit_id for c in changes}

    # PRs that include those commits
    pr_ids = set()
    if commit_ids:
        pr_commit_rows = (await session.execute(
            select(Relationship).where(
                Relationship.repository_id == repo_id,
                Relationship.source_type == "pull_request",
                Relationship.target_type == "commit",
                Relationship.target_id.in_(list(commit_ids)),
            ).limit(20)
        )).scalars().all()
        pr_ids = {r.source_id for r in pr_commit_rows}

    results = []

    # Fetch those PRs
    if pr_ids:
        prs = (await session.execute(
            select(PullRequest).where(PullRequest.id.in_(list(pr_ids)))
        )).scalars().all()
        for pr in prs:
            results.append({
                "source_type": "pull_request",
                "source_id": pr.id,
                "title": pr.title,
                "snippet": (pr.body or "")[:400],
                "author": pr.author_login,
                "date": pr.created_at,
                "github_url": pr.github_url,
                "graph_score": 0.85,
                "why_selected": f"PR includes commit touching {file_path}",
            })

    return results


def _rerank(candidates: list[dict], question: str, file_path: Optional[str]) -> list[dict]:
    """
    final_score = 0.45*semantic + 0.20*keyword + 0.20*graph + 0.10*source_quality + 0.05*recency
    """
    question_words = set(question.lower().split())

    for item in candidates:
        semantic = item.get("semantic_score", 0.0)
        keyword = item.get("keyword_score", 0.0)
        graph = item.get("graph_score", 0.0)
        source_q = SOURCE_QUALITY.get(item["source_type"], 0.5)

        # Recency: normalize against 5 years
        date = item.get("date")
        recency = 0.5
        if date:
            try:
                age_days = (datetime.utcnow() - date).days
                recency = max(0.0, 1.0 - age_days / 1825)
            except Exception:
                pass

        # Keyword bonus based on snippet
        snippet_words = set((item.get("snippet", "") + " " + item.get("title", "")).lower().split())
        if question_words:
            kw_bonus = len(question_words & snippet_words) / len(question_words)
            keyword = max(keyword, kw_bonus * 0.8)

        item["final_score"] = (
            0.45 * semantic
            + 0.20 * keyword
            + 0.20 * graph
            + 0.10 * source_q
            + 0.05 * recency
        )

    return sorted(candidates, key=lambda x: x.get("final_score", 0), reverse=True)
