"""
Builds relationship graph between commits, PRs, issues, files, and code chunks.
"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from ..models import Relationship, Commit, PullRequest, Issue, CommitFileChange, File, PullRequestCommit

ISSUE_REF = re.compile(r'(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*#(\d+)', re.IGNORECASE)
ANY_HASH_REF = re.compile(r'#(\d+)')


def _add_relationship(session: Session, repo_id: str, src_type: str, src_id: str,
                       tgt_type: str, tgt_id: str, rel_type: str,
                       confidence: float = 1.0, evidence: Optional[str] = None):
    # Avoid exact duplicates
    existing = session.execute(
        select(Relationship).where(
            Relationship.repository_id == repo_id,
            Relationship.source_type == src_type,
            Relationship.source_id == src_id,
            Relationship.target_type == tgt_type,
            Relationship.target_id == tgt_id,
            Relationship.relationship_type == rel_type,
        )
    ).first()
    if existing:
        return

    rel = Relationship(
        repository_id=repo_id,
        source_type=src_type,
        source_id=src_id,
        target_type=tgt_type,
        target_id=tgt_id,
        relationship_type=rel_type,
        confidence=confidence,
        evidence=evidence,
    )
    session.add(rel)


def build_relationships(session: Session, repo_id: str):
    """Builds all graph relationships for a repository. Uses sync session."""

    # 1. commit modifies file
    changes = session.execute(
        select(CommitFileChange).where(CommitFileChange.repository_id == repo_id)
    ).scalars().all()

    for change in changes:
        if change.file_id:
            _add_relationship(
                session, repo_id,
                "commit", change.commit_id,
                "file", change.file_id,
                "modifies",
            )

    # 2. PR includes commit
    pr_commits = session.execute(
        select(PullRequestCommit)
        .join(PullRequest, PullRequest.id == PullRequestCommit.pull_request_id)
        .where(PullRequest.repository_id == repo_id)
    ).scalars().all()

    for prc in pr_commits:
        _add_relationship(
            session, repo_id,
            "pull_request", prc.pull_request_id,
            "commit", prc.commit_id,
            "includes",
        )

    # 3. PR references issue (from body/title)
    prs = session.execute(
        select(PullRequest).where(PullRequest.repository_id == repo_id)
    ).scalars().all()

    issue_number_to_id: dict[int, str] = {}
    issues = session.execute(
        select(Issue).where(Issue.repository_id == repo_id)
    ).scalars().all()
    for issue in issues:
        issue_number_to_id[issue.github_issue_number] = issue.id

    for pr in prs:
        text_to_search = f"{pr.title or ''} {pr.body or ''}"
        for num in {int(m) for m in ISSUE_REF.findall(text_to_search)}:
            if num in issue_number_to_id:
                _add_relationship(
                    session, repo_id,
                    "pull_request", pr.id,
                    "issue", issue_number_to_id[num],
                    "fixes",
                    confidence=0.9,
                    evidence=f"PR body references #{num}",
                )

        # Weaker: any #N mention
        for num in {int(m) for m in ANY_HASH_REF.findall(text_to_search)}:
            if num in issue_number_to_id:
                _add_relationship(
                    session, repo_id,
                    "pull_request", pr.id,
                    "issue", issue_number_to_id[num],
                    "references",
                    confidence=0.6,
                    evidence=f"PR mentions #{num}",
                )

    # 4. Commit references issue
    commits = session.execute(
        select(Commit).where(Commit.repository_id == repo_id)
    ).scalars().all()

    for commit in commits:
        text_to_search = commit.message or ""
        for num in {int(m) for m in ISSUE_REF.findall(text_to_search)}:
            if num in issue_number_to_id:
                _add_relationship(
                    session, repo_id,
                    "commit", commit.id,
                    "issue", issue_number_to_id[num],
                    "fixes",
                    confidence=0.85,
                    evidence=f"Commit message references #{num}",
                )

    session.commit()
