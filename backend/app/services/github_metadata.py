"""
Fetches PRs, issues, comments, and commit metadata from GitHub REST API.
"""
import re
import asyncio
import httpx
from typing import Optional
from datetime import datetime

ISSUE_REF_PATTERN = re.compile(r'(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*#(\d+)', re.IGNORECASE)
MENTION_PATTERN = re.compile(r'#(\d+)')


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._headers = headers

    async def _get(self, path: str, params: dict = None) -> dict | list | None:
        url = f"{self.BASE}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self._headers, params=params or {})
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def _paginate(self, path: str, params: dict = None, max_pages: int = 20) -> list:
        items = []
        p = dict(params or {})
        p.setdefault("per_page", 100)
        for page in range(1, max_pages + 1):
            p["page"] = page
            data = await self._get(path, p)
            if not data:
                break
            items.extend(data)
            if len(data) < p["per_page"]:
                break
        return items

    async def get_repo_info(self) -> dict:
        return await self._get(f"/repos/{self.owner}/{self.repo}") or {}

    async def get_pull_requests(self, state: str = "all") -> list[dict]:
        return await self._paginate(
            f"/repos/{self.owner}/{self.repo}/pulls",
            {"state": state, "sort": "created", "direction": "desc"},
        )

    async def get_pr_commits(self, pr_number: int) -> list[dict]:
        return await self._paginate(
            f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/commits"
        )

    async def get_pr_comments(self, pr_number: int) -> list[dict]:
        # Review comments (inline)
        review = await self._paginate(
            f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/comments"
        )
        # Issue comments (general PR discussion)
        issue = await self._paginate(
            f"/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments"
        )
        return review + issue

    async def get_issues(self, state: str = "all") -> list[dict]:
        all_items = await self._paginate(
            f"/repos/{self.owner}/{self.repo}/issues",
            {"state": state, "sort": "created", "direction": "desc"},
        )
        # Filter out pull requests (they appear in issues endpoint too)
        return [i for i in all_items if "pull_request" not in i]

    async def get_issue_comments(self, issue_number: int) -> list[dict]:
        return await self._paginate(
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments"
        )

    async def get_commit(self, sha: str) -> dict:
        return await self._get(f"/repos/{self.owner}/{self.repo}/commits/{sha}") or {}


def extract_issue_refs(text: str) -> list[int]:
    """Extracts issue numbers from 'fixes #123' style references."""
    return [int(m) for m in ISSUE_REF_PATTERN.findall(text or "")]


def extract_all_issue_mentions(text: str) -> list[int]:
    return [int(m) for m in MENTION_PATTERN.findall(text or "")]


def parse_datetime(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None
