"""
Orchestrates the full repository ingestion pipeline.
Runs synchronously inside a Celery worker.
"""
import os
import re
import hashlib
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import (
    Repository, IngestionJob, File, CodeChunk, Commit,
    CommitFileChange, PullRequest, PullRequestCommit, Issue, Comment, Document
)
from ..services.code_chunker import chunk_file
from ..services.git_history import GitHistoryService
from ..config import get_settings

settings = get_settings()

IGNORE_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "target",
    "vendor", "__pycache__", ".venv", "venv", ".env", "coverage",
    ".cache", ".idea", ".vscode",
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "Gemfile.lock",
    ".DS_Store", "*.min.js", "*.min.css",
}
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".kt",
    ".rs", ".cpp", ".cc", ".c", ".h", ".rb", ".php",
    ".md", ".txt", ".yaml", ".yml", ".toml", ".json",
    ".sh", ".bash", ".zsh",
}


def _should_ignore(path: str) -> bool:
    parts = path.split("/")
    for part in parts[:-1]:
        if part in IGNORE_DIRS or part.startswith("."):
            return True
    filename = parts[-1]
    if filename in IGNORE_FILES:
        return True
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in SUPPORTED_EXTENSIONS:
        return True
    return False


def _detect_language(path: str) -> str:
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        ".py": "python", ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".go": "go",
        ".java": "java", ".kt": "kotlin", ".rs": "rust",
        ".cpp": "cpp", ".cc": "cpp", ".c": "c", ".h": "c",
        ".rb": "ruby", ".php": "php",
        ".md": "markdown", ".txt": "text",
        ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
        ".json": "json", ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    }.get(ext, "unknown")


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _log(session: Session, job: IngestionJob, stage: str, message: str, pct: int):
    job.current_stage = stage
    job.progress_percent = pct
    if job.logs is None:
        job.logs = []
    job.logs = job.logs + [{"ts": datetime.utcnow().isoformat(), "stage": stage, "msg": message}]
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    print(f"[{pct}%] {stage}: {message}")


def run_ingestion(repo_id: str, github_token: Optional[str] = None):
    """Main ingestion entrypoint called by Celery worker."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        repo = session.execute(select(Repository).where(Repository.id == repo_id)).scalar_one()
        job = session.execute(
            select(IngestionJob).where(IngestionJob.repository_id == repo_id)
            .order_by(IngestionJob.created_at.desc())
        ).scalar_one()

        repo.status = "ingesting"
        job.status = "running"
        session.commit()

        # --- Stage 1: Clone ---
        _log(session, job, "cloning", f"Cloning {repo.github_url}", 5)
        repo_path = os.path.join(settings.repos_path, repo_id)
        token_url = repo.github_url
        if github_token:
            # Inject token into clone URL
            token_url = repo.github_url.replace(
                "https://", f"https://x-access-token:{github_token}@"
            )
        git_svc = GitHistoryService.__new__(GitHistoryService)
        git_svc = git_svc.clone_or_pull(token_url, repo_path)
        repo.local_path = repo_path
        repo.default_branch = git_svc.get_default_branch()
        session.commit()

        # --- Stage 2: File tree ---
        _log(session, job, "parsing_files", "Parsing file tree", 15)
        raw_files = git_svc.list_files(repo.default_branch)
        file_map: dict[str, str] = {}  # path -> file_id

        existing_files = session.execute(
            select(File).where(File.repository_id == repo_id)
        ).scalars().all()
        existing_file_map = {f.path: f for f in existing_files}

        for raw in raw_files:
            path = raw["path"]
            if _should_ignore(path):
                continue

            content = git_svc.read_file(repo.default_branch, path) or ""
            content_hash = _hash_content(content)
            lines = content.count("\n") + 1

            if path in existing_file_map:
                f = existing_file_map[path]
                f.current_hash = content_hash
                f.size_bytes = raw.get("size_bytes", len(content.encode()))
                f.line_count = lines
            else:
                f = File(
                    repository_id=repo_id,
                    path=path,
                    language=_detect_language(path),
                    size_bytes=raw.get("size_bytes", len(content.encode())),
                    current_hash=content_hash,
                    line_count=lines,
                )
                session.add(f)

            session.flush()
            file_map[path] = f.id

        session.commit()

        # --- Stage 3: Code chunking ---
        _log(session, job, "chunking", "Chunking source code", 25)
        # Delete old chunks for this repo
        old_chunks = session.execute(
            select(CodeChunk).where(CodeChunk.repository_id == repo_id)
        ).scalars().all()
        for c in old_chunks:
            session.delete(c)
        session.commit()

        chunk_texts: list[str] = []
        chunk_records: list[CodeChunk] = []

        for raw in raw_files:
            path = raw["path"]
            if _should_ignore(path) or path not in file_map:
                continue
            content = git_svc.read_file(repo.default_branch, path) or ""
            if not content.strip():
                continue

            chunks = chunk_file(path, content)
            for chunk in chunks:
                record = CodeChunk(
                    repository_id=repo_id,
                    file_id=file_map[path],
                    symbol_name=chunk.symbol_name,
                    symbol_type=chunk.symbol_type,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content=chunk.content,
                    content_hash=chunk.content_hash,
                )
                session.add(record)
                chunk_texts.append(f"File: {path}\n{chunk.content[:2000]}")
                chunk_records.append(record)

        session.commit()

        # --- Stage 4: Git history ---
        _log(session, job, "git_history", "Reading git commit history", 35)
        # Delete old commits
        old_commits = session.execute(
            select(Commit).where(Commit.repository_id == repo_id)
        ).scalars().all()
        for c in old_commits:
            session.delete(c)
        session.commit()

        commit_sha_to_id: dict[str, str] = {}
        commit_batch = []
        for commit_data in git_svc.iter_commits(repo.default_branch, max_count=3000):
            c = Commit(
                repository_id=repo_id,
                sha=commit_data["sha"],
                message=commit_data["message"],
                author_name=commit_data["author_name"],
                author_email=commit_data["author_email"],
                committed_at=commit_data["committed_at"],
            )
            session.add(c)
            commit_batch.append(c)

        session.flush()
        for c in commit_batch:
            commit_sha_to_id[c.sha] = c.id

        session.commit()

        # --- Stage 5: Commit file changes ---
        _log(session, job, "commit_changes", "Indexing commit file changes", 45)
        for sha, cid in list(commit_sha_to_id.items())[:500]:  # limit for MVP
            changes = git_svc.get_commit_file_changes(sha)
            for ch in changes:
                fid = file_map.get(ch["file_path"])
                record = CommitFileChange(
                    repository_id=repo_id,
                    commit_id=cid,
                    file_id=fid,
                    file_path=ch["file_path"],
                    status=ch["status"],
                    additions=ch["additions"],
                    deletions=ch["deletions"],
                    patch=ch["patch"],
                )
                session.add(record)

        session.commit()

        # Update file churn scores
        _log(session, job, "churn", "Computing file churn scores", 50)
        from sqlalchemy import text as sql_text
        session.execute(sql_text("""
            UPDATE files f
            SET churn_score = sub.total_churn,
                author_count = sub.authors
            FROM (
                SELECT cfc.file_id,
                       SUM(cfc.additions + cfc.deletions) as total_churn,
                       COUNT(DISTINCT c.author_email) as authors
                FROM commit_file_changes cfc
                JOIN commits c ON c.id = cfc.commit_id
                WHERE cfc.repository_id = :repo_id AND cfc.file_id IS NOT NULL
                GROUP BY cfc.file_id
            ) sub
            WHERE f.id = sub.file_id AND f.repository_id = :repo_id
        """), {"repo_id": repo_id})
        session.commit()

        # --- Stage 6: GitHub PRs ---
        _log(session, job, "github_prs", "Fetching GitHub pull requests", 55)
        if repo.include_pr_comments or repo.include_issues:
            try:
                import asyncio
                asyncio.run(_fetch_github_data(
                    session, repo, commit_sha_to_id, github_token
                ))
            except Exception as e:
                _log(session, job, "github_prs", f"GitHub API error (skipping): {e}", 65)

        # --- Stage 7: Build relationships ---
        _log(session, job, "relationships", "Building relationship graph", 75)
        from ..services.relationship_builder import build_relationships
        build_relationships(session, repo_id)

        # --- Stage 8: Embeddings ---
        _log(session, job, "embeddings", "Generating embeddings", 80)
        try:
            import asyncio
            asyncio.run(_embed_all(session, repo_id, chunk_texts, chunk_records))
        except Exception as e:
            _log(session, job, "embeddings", f"Embedding error (skipping): {e}", 90)

        # --- Done ---
        _log(session, job, "ready", "Ingestion complete", 100)
        repo.status = "ready"
        job.status = "completed"
        job.progress_percent = 100
        session.commit()

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            repo = session.execute(select(Repository).where(Repository.id == repo_id)).scalar_one()
            job = session.execute(
                select(IngestionJob).where(IngestionJob.repository_id == repo_id)
                .order_by(IngestionJob.created_at.desc())
            ).scalar_one()
            repo.status = "failed"
            job.status = "failed"
            job.error_message = f"{str(e)}\n\n{tb}"
            session.commit()
        except Exception:
            pass
        raise
    finally:
        session.close()


async def _fetch_github_data(
    session, repo: Repository, commit_sha_to_id: dict, github_token: Optional[str]
):
    """Fetches PRs, issues, comments from GitHub API."""
    from ..services.github_metadata import GitHubClient, parse_datetime, extract_issue_refs

    client = GitHubClient(repo.owner, repo.name, github_token)

    # Fetch PRs
    prs_data = await client.get_pull_requests("all")
    pr_number_to_id: dict[int, str] = {}

    for pr_data in prs_data[:200]:  # limit for MVP
        pr = PullRequest(
            repository_id=repo.id,
            github_pr_number=pr_data["number"],
            title=pr_data.get("title", ""),
            body=pr_data.get("body", "") or "",
            state=pr_data.get("state", "open"),
            author_login=(pr_data.get("user") or {}).get("login", ""),
            merged=pr_data.get("merged_at") is not None,
            merged_at=parse_datetime(pr_data.get("merged_at")),
            created_at=parse_datetime(pr_data.get("created_at")),
            updated_at=parse_datetime(pr_data.get("updated_at")),
            github_url=pr_data.get("html_url", ""),
        )
        session.add(pr)
        session.flush()
        pr_number_to_id[pr.github_pr_number] = pr.id

        # Link PR to commits
        try:
            pr_commits = await client.get_pr_commits(pr.github_pr_number)
            for pc in pr_commits:
                sha = pc.get("sha", "")
                if sha in commit_sha_to_id:
                    prc = PullRequestCommit(
                        pull_request_id=pr.id,
                        commit_id=commit_sha_to_id[sha],
                    )
                    session.add(prc)
        except Exception:
            pass

        # Fetch PR comments
        if repo.include_pr_comments:
            try:
                comments = await client.get_pr_comments(pr.github_pr_number)
                for c_data in comments[:50]:
                    comment = Comment(
                        repository_id=repo.id,
                        source_type="pull_request",
                        source_id=pr.id,
                        author_login=(c_data.get("user") or {}).get("login", ""),
                        body=c_data.get("body", "") or "",
                        created_at=parse_datetime(c_data.get("created_at")),
                        github_url=c_data.get("html_url", ""),
                    )
                    session.add(comment)
            except Exception:
                pass

    session.commit()

    # Fetch issues
    if repo.include_issues:
        issues_data = await client.get_issues("all")
        for issue_data in issues_data[:200]:
            issue = Issue(
                repository_id=repo.id,
                github_issue_number=issue_data["number"],
                title=issue_data.get("title", ""),
                body=issue_data.get("body", "") or "",
                state=issue_data.get("state", "open"),
                author_login=(issue_data.get("user") or {}).get("login", ""),
                labels=[l["name"] for l in (issue_data.get("labels") or [])],
                created_at=parse_datetime(issue_data.get("created_at")),
                updated_at=parse_datetime(issue_data.get("updated_at")),
                closed_at=parse_datetime(issue_data.get("closed_at")),
                github_url=issue_data.get("html_url", ""),
            )
            session.add(issue)
            session.flush()

            # Issue comments
            try:
                comments = await client.get_issue_comments(issue.github_issue_number)
                for c_data in comments[:30]:
                    comment = Comment(
                        repository_id=repo.id,
                        source_type="issue",
                        source_id=issue.id,
                        author_login=(c_data.get("user") or {}).get("login", ""),
                        body=c_data.get("body", "") or "",
                        created_at=parse_datetime(c_data.get("created_at")),
                        github_url=c_data.get("html_url", ""),
                    )
                    session.add(comment)
            except Exception:
                pass

        session.commit()


async def _embed_all(session, repo_id: str, chunk_texts: list[str], chunk_records: list):
    """Batch-embeds code chunks, PRs, issues, comments."""
    from ..services.embeddings import embed_texts
    from ..models import PullRequest, Issue, Comment

    # Embed code chunks in batches
    BATCH = 50
    for i in range(0, len(chunk_texts), BATCH):
        batch_texts = chunk_texts[i: i + BATCH]
        batch_records = chunk_records[i: i + BATCH]
        embeddings = await embed_texts(batch_texts)
        for record, emb in zip(batch_records, embeddings):
            if emb:
                record.embedding = emb
                session.add(record)

    session.commit()

    # Embed PRs
    prs = session.execute(
        select(PullRequest).where(PullRequest.repository_id == repo_id)
    ).scalars().all()
    pr_texts = [f"{p.title}\n{(p.body or '')[:1000]}" for p in prs]
    if pr_texts:
        pr_embeddings = await embed_texts(pr_texts)
        for pr, emb in zip(prs, pr_embeddings):
            if emb:
                pr.embedding = emb
                session.add(pr)
        session.commit()

    # Embed issues
    issues = session.execute(
        select(Issue).where(Issue.repository_id == repo_id, Issue.embedding == None)
    ).scalars().all()
    issue_texts = [f"{i.title}\n{(i.body or '')[:1000]}" for i in issues]
    if issue_texts:
        issue_embeddings = await embed_texts(issue_texts)
        for issue, emb in zip(issues, issue_embeddings):
            if emb:
                issue.embedding = emb
                session.add(issue)
        session.commit()

    # Embed comments
    comments = session.execute(
        select(Comment).where(Comment.repository_id == repo_id, Comment.embedding == None)
    ).scalars().all()
    comment_texts = [(c.body or "")[:1000] for c in comments]
    if comment_texts:
        comment_embeddings = await embed_texts(comment_texts)
        for comment, emb in zip(comments, comment_embeddings):
            if emb:
                comment.embedding = emb
                session.add(comment)
        session.commit()
