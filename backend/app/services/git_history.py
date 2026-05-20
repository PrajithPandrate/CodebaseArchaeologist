"""
Extracts commit history, file changes, churn, and blame info using GitPython.
"""
import os
from typing import Optional
from datetime import datetime
from git import Repo, InvalidGitRepositoryError
from ..services.redaction import redact_secrets


class GitHistoryService:
    def __init__(self, repo_path: str):
        self.repo = Repo(repo_path)

    def get_default_branch(self) -> str:
        try:
            return self.repo.active_branch.name
        except Exception:
            for name in ("main", "master", "develop"):
                try:
                    self.repo.refs[name]
                    return name
                except Exception:
                    pass
            return "main"

    def iter_commits(self, branch: str = "HEAD", max_count: int = 5000):
        """Yields dicts with commit metadata."""
        try:
            for commit in self.repo.iter_commits(branch, max_count=max_count):
                yield {
                    "sha": commit.hexsha,
                    "message": redact_secrets(commit.message.strip()),
                    "author_name": commit.author.name or "",
                    "author_email": commit.author.email or "",
                    "committed_at": datetime.utcfromtimestamp(commit.committed_date),
                }
        except Exception as e:
            print(f"Error iterating commits: {e}")

    def get_commit_file_changes(self, sha: str) -> list[dict]:
        """Returns list of file change dicts for a commit."""
        try:
            commit = self.repo.commit(sha)
            changes = []

            if not commit.parents:
                # Initial commit — everything is "added"
                for item in commit.tree.traverse():
                    if item.type == "blob":
                        changes.append({
                            "file_path": item.path,
                            "status": "added",
                            "additions": 0,
                            "deletions": 0,
                            "patch": None,
                        })
                return changes

            parent = commit.parents[0]
            diffs = parent.diff(commit, create_patch=True)
            for diff in diffs:
                status = "modified"
                if diff.new_file:
                    status = "added"
                elif diff.deleted_file:
                    status = "deleted"
                elif diff.renamed_file:
                    status = "renamed"

                patch_text = None
                try:
                    raw = diff.diff
                    if isinstance(raw, bytes):
                        patch_text = raw.decode("utf-8", errors="replace")
                    else:
                        patch_text = raw
                    if patch_text:
                        patch_text = redact_secrets(patch_text[:10000])
                except Exception:
                    pass

                additions = patch_text.count("\n+") if patch_text else 0
                deletions = patch_text.count("\n-") if patch_text else 0

                changes.append({
                    "file_path": diff.b_path or diff.a_path,
                    "status": status,
                    "additions": additions,
                    "deletions": deletions,
                    "patch": patch_text,
                })

            return changes
        except Exception as e:
            print(f"Error getting file changes for {sha}: {e}")
            return []

    def list_files(self, branch: str = "HEAD") -> list[dict]:
        """Lists all tracked files with basic metadata."""
        files = []
        try:
            tree = self.repo.commit(branch).tree
            for item in tree.traverse():
                if item.type == "blob":
                    try:
                        size = item.data_stream.size if hasattr(item.data_stream, "size") else 0
                        files.append({
                            "path": item.path,
                            "size_bytes": size,
                        })
                    except Exception:
                        files.append({"path": item.path, "size_bytes": 0})
        except Exception as e:
            print(f"Error listing files: {e}")
        return files

    def read_file(self, branch: str, file_path: str) -> Optional[str]:
        """Reads file content from a specific commit/branch."""
        try:
            commit = self.repo.commit(branch)
            blob = commit.tree / file_path
            content = blob.data_stream.read().decode("utf-8", errors="replace")
            return content
        except Exception:
            return None

    def get_file_log(self, file_path: str, max_count: int = 100) -> list[dict]:
        """Returns commit history for a specific file."""
        commits = []
        try:
            for commit in self.repo.iter_commits("HEAD", paths=file_path, max_count=max_count):
                commits.append({
                    "sha": commit.hexsha,
                    "message": redact_secrets(commit.message.strip()),
                    "author_name": commit.author.name or "",
                    "author_email": commit.author.email or "",
                    "committed_at": datetime.utcfromtimestamp(commit.committed_date),
                })
        except Exception as e:
            print(f"Error getting file log for {file_path}: {e}")
        return commits

    def clone_or_pull(self, github_url: str, dest_path: str) -> "GitHistoryService":
        """Clones repo if not exists, pulls if it does."""
        if os.path.exists(os.path.join(dest_path, ".git")):
            repo = Repo(dest_path)
            repo.remotes.origin.pull()
        else:
            os.makedirs(dest_path, exist_ok=True)
            Repo.clone_from(github_url, dest_path)

        return GitHistoryService(dest_path)
