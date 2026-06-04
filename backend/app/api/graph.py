from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..database import get_session
from ..models import Relationship, Commit, PullRequest, Issue, File, CommitFileChange

router = APIRouter(prefix="/api/repositories/{repo_id}/graph", tags=["graph"])


@router.get("")
async def get_knowledge_graph(
    repo_id: str,
    file_path: Optional[str] = Query(None),
    symbol_name: Optional[str] = Query(None),
    depth: int = Query(2, ge=1, le=3),
    relationship_types: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Returns nodes and edges for the knowledge graph."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    rel_filter = set(relationship_types.split(",")) if relationship_types else None

    # Get relationships for this repo
    rel_query = select(Relationship).where(Relationship.repository_id == repo_id)
    if rel_filter:
        rel_query = rel_query.where(Relationship.relationship_type.in_(list(rel_filter)))

    rels = (await session.execute(rel_query.limit(500))).scalars().all()

    # If file_path filter, start from that file and expand
    seed_ids: set[str] = set()
    if file_path:
        file_row = (await session.execute(
            select(File).where(File.repository_id == repo_id, File.path == file_path)
        )).scalar_one_or_none()
        if file_row:
            seed_ids.add(file_row.id)
            nodes[file_row.id] = {
                "id": file_row.id,
                "type": "file",
                "label": file_row.path.split("/")[-1],
                "data": {"path": file_row.path, "language": file_row.language},
            }

    for rel in rels:
        # Filter by seed if provided
        if seed_ids and rel.source_id not in seed_ids and rel.target_id not in seed_ids:
            continue

        edge = {
            "id": rel.id,
            "source": rel.source_id,
            "target": rel.target_id,
            "type": rel.relationship_type,
            "confidence": rel.confidence,
        }
        edges.append(edge)

        # Add source node
        if rel.source_id not in nodes:
            nodes[rel.source_id] = await _make_node(session, rel.source_type, rel.source_id)

        # Add target node
        if rel.target_id not in nodes:
            nodes[rel.target_id] = await _make_node(session, rel.target_type, rel.target_id)

        # Expand seeds to 2nd degree
        if seed_ids:
            seed_ids.add(rel.source_id)
            seed_ids.add(rel.target_id)

    # If no seeds and no results, return top nodes
    if not seed_ids and not nodes:
        files = (await session.execute(
            select(File).where(File.repository_id == repo_id)
            .order_by(File.churn_score.desc()).limit(20)
        )).scalars().all()
        for f in files:
            nodes[f.id] = {
                "id": f.id,
                "type": "file",
                "label": f.path.split("/")[-1],
                "data": {"path": f.path, "language": f.language, "churn": f.churn_score},
            }

    return {
        "nodes": list(nodes.values()),
        "edges": edges[:300],
    }


async def _make_node(session: AsyncSession, node_type: str, node_id: str) -> dict:
    label = node_id[:12]
    data = {}

    if node_type == "commit":
        row = (await session.execute(
            select(Commit).where(Commit.id == node_id)
        )).scalar_one_or_none()
        if row:
            label = row.message.splitlines()[0][:40]
            data = {"sha": row.sha[:8], "author": row.author_name}
    elif node_type == "pull_request":
        row = (await session.execute(
            select(PullRequest).where(PullRequest.id == node_id)
        )).scalar_one_or_none()
        if row:
            label = f"PR #{row.github_pr_number}"
            data = {"title": row.title[:60], "merged": row.merged}
    elif node_type == "issue":
        row = (await session.execute(
            select(Issue).where(Issue.id == node_id)
        )).scalar_one_or_none()
        if row:
            label = f"#{row.github_issue_number}"
            data = {"title": row.title[:60], "state": row.state}
    elif node_type == "file":
        row = (await session.execute(
            select(File).where(File.id == node_id)
        )).scalar_one_or_none()
        if row:
            label = row.path.split("/")[-1]
            data = {"path": row.path}

    return {"id": node_id, "type": node_type, "label": label, "data": data}
