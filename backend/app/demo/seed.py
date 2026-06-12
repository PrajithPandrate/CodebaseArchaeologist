"""
Seeds realistic demo data: a payment service with retry logic history.
Use this for showcase when live GitHub API is not configured.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import (
    Repository, IngestionJob, File, CodeChunk, Commit, CommitFileChange,
    PullRequest, PullRequestCommit, Issue, Comment, Relationship
)

DEMO_OWNER = "acme-corp"
DEMO_REPO = "payment-service"
DEMO_URL = f"https://github.com/{DEMO_OWNER}/{DEMO_REPO}"


async def seed_demo_data(session: AsyncSession) -> str:
    # Check if demo already exists
    existing = (await session.execute(
        select(Repository).where(
            Repository.owner == DEMO_OWNER,
            Repository.name == DEMO_REPO,
        )
    )).scalar_one_or_none()

    if existing:
        return existing.id

    repo = Repository(
        owner=DEMO_OWNER,
        name=DEMO_REPO,
        github_url=DEMO_URL,
        default_branch="main",
        local_path=None,
        status="ready",
        include_issues=True,
        include_pr_comments=True,
        include_commit_diffs=True,
        include_docs=True,
    )
    session.add(repo)
    await session.flush()
    repo_id = repo.id

    job = IngestionJob(
        repository_id=repo_id,
        status="completed",
        current_stage="ready",
        progress_percent=100,
        logs=[{"ts": datetime.utcnow().isoformat(), "stage": "ready", "msg": "Demo data seeded"}],
    )
    session.add(job)

    # ---- Files ----
    base = datetime(2023, 1, 15)

    files_data = [
        ("src/payments/retry.py", "python", 247),
        ("src/payments/charge.py", "python", 189),
        ("src/payments/idempotency.py", "python", 134),
        ("src/payments/webhook.py", "python", 312),
        ("src/orders/fulfillment.py", "python", 201),
        ("src/database/models.py", "python", 445),
        ("tests/test_payments.py", "python", 198),
        ("README.md", "markdown", 87),
    ]

    file_ids: dict[str, str] = {}
    for path, lang, lines in files_data:
        f = File(
            repository_id=repo_id,
            path=path,
            language=lang,
            size_bytes=lines * 40,
            line_count=lines,
            churn_score=float(lines // 3),
            author_count=3 if "retry" in path or "charge" in path else 1,
        )
        session.add(f)
        await session.flush()
        file_ids[path] = f.id

    # ---- Code chunks (key retry logic function) ----
    retry_content = '''def retry_payment(payment_id: str, max_retries: int = 3) -> PaymentResult:
    """
    Retries a failed payment with exponential backoff.
    Uses idempotency keys to prevent duplicate charges on timeout.

    Added in PR #47 after incident INC-2023-089 where customers
    were charged twice due to network timeouts during payment processing.
    """
    idempotency_key = get_idempotency_key(payment_id)

    for attempt in range(max_retries):
        try:
            result = charge_payment(payment_id, idempotency_key=idempotency_key)
            if result.success:
                return result
        except NetworkTimeoutError:
            if attempt == max_retries - 1:
                raise
            backoff = 2 ** attempt
            time.sleep(backoff)
        except DuplicateChargeError:
            # Payment already succeeded on a previous attempt
            return PaymentResult(success=True, idempotent=True)

    raise MaxRetriesExceededError(f"Payment {payment_id} failed after {max_retries} attempts")'''

    chunk = CodeChunk(
        repository_id=repo_id,
        file_id=file_ids["src/payments/retry.py"],
        symbol_name="retry_payment",
        symbol_type="function",
        start_line=42,
        end_line=68,
        content=retry_content,
        content_hash="demo_retry_001",
    )
    session.add(chunk)

    idempotency_content = '''def get_idempotency_key(payment_id: str) -> str:
    """
    Returns a stable idempotency key for a payment attempt.
    Prevents duplicate charges when retrying after network failures.
    Key is derived from payment_id + current date to expire after 24h.
    """
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return f"pay_{payment_id}_{date_str}"'''

    chunk2 = CodeChunk(
        repository_id=repo_id,
        file_id=file_ids["src/payments/idempotency.py"],
        symbol_name="get_idempotency_key",
        symbol_type="function",
        start_line=18,
        end_line=27,
        content=idempotency_content,
        content_hash="demo_idempotency_001",
    )
    session.add(chunk2)

    # ---- Commits ----
    commits_data = [
        (base - timedelta(days=180), "Initial payment service setup", "sarah@acme.com", "Sarah Chen"),
        (base - timedelta(days=120), "Add basic charge endpoint", "sarah@acme.com", "Sarah Chen"),
        (base - timedelta(days=90), "Fix payment timeout handling", "raj@acme.com", "Raj Patel"),
        (base - timedelta(days=60), "Add idempotency key support for retries", "raj@acme.com", "Raj Patel"),
        (base - timedelta(days=58), "Prevent duplicate charge on timeout retry", "raj@acme.com", "Raj Patel"),
        (base - timedelta(days=45), "Add retry logic with exponential backoff", "raj@acme.com", "Raj Patel"),
        (base - timedelta(days=30), "Fix webhook retry causing stale order status", "maria@acme.com", "Maria Santos"),
        (base - timedelta(days=15), "Add test coverage for retry scenarios", "sarah@acme.com", "Sarah Chen"),
        (base - timedelta(days=5), "Refactor retry: extract idempotency module", "raj@acme.com", "Raj Patel"),
    ]

    commit_ids = []
    for ts, msg, email, name in commits_data:
        c = Commit(
            repository_id=repo_id,
            sha=str(uuid.uuid4()).replace("-", "")[:40],
            message=msg,
            author_name=name,
            author_email=email,
            committed_at=ts,
            github_url=f"{DEMO_URL}/commit/{uuid.uuid4().hex[:8]}",
        )
        session.add(c)
        await session.flush()
        commit_ids.append(c.id)

    # File changes for key commits
    for commit_id in commit_ids[3:6]:
        for path in ["src/payments/retry.py", "src/payments/idempotency.py"]:
            change = CommitFileChange(
                repository_id=repo_id,
                commit_id=commit_id,
                file_id=file_ids[path],
                file_path=path,
                status="modified",
                additions=25,
                deletions=8,
            )
            session.add(change)

    # ---- Issues ----
    issue1 = Issue(
        repository_id=repo_id,
        github_issue_number=89,
        title="Customers seeing duplicate payment confirmations",
        body="""**Bug Report**

        Multiple customers (3 reports in last 24h) are receiving duplicate payment confirmation emails and being charged twice.

        **Steps to reproduce:**
        1. Customer initiates payment
        2. Network timeout occurs during processing
        3. Customer retries payment
        4. Both the original and retry charge go through

        **Impact:** High - affects revenue and customer trust
        **Reported by:** Customer Support team

        This seems to happen when the payment processor times out but the charge actually went through on their end.""",
        state="closed",
        author_login="alice-ops",
        labels=["bug", "payment", "critical"],
        created_at=base - timedelta(days=62),
        closed_at=base - timedelta(days=55),
        github_url=f"{DEMO_URL}/issues/89",
    )
    session.add(issue1)
    await session.flush()

    issue2 = Issue(
        repository_id=repo_id,
        github_issue_number=124,
        title="Webhook retries causing stale order status",
        body="""After the payment retry fix in PR #47, we're seeing a new issue:
        when payment webhooks fail and get retried, order fulfillment is triggered multiple times.

        This leads to orders being marked as 'fulfilled' before they actually ship, because the
        fulfillment webhook fires on the first webhook delivery attempt, and then fires again on retry.

        Related to: #89 (the fix for that issue introduced this regression)""",
        state="closed",
        author_login="bob-backend",
        labels=["bug", "webhook", "orders"],
        created_at=base - timedelta(days=32),
        closed_at=base - timedelta(days=28),
        github_url=f"{DEMO_URL}/issues/124",
    )
    session.add(issue2)
    await session.flush()

    # ---- Pull Requests ----
    pr1 = PullRequest(
        repository_id=repo_id,
        github_pr_number=47,
        title="Add idempotency key handling for payment retries",
        body="""## Problem

        Fixes #89 - Customers are being charged twice when payment requests timeout.

        ## Root Cause

        When a payment request times out, the charge may have succeeded on Stripe's end but we
        never received the confirmation. When the customer retries, we initiate a new charge.

        ## Solution

        1. Generate stable idempotency keys tied to payment_id + date
        2. Always pass idempotency key to Stripe API
        3. Catch `DuplicateChargeError` and treat as success
        4. Add exponential backoff (1s, 2s, 4s) between retries

        ## Testing
        - Unit tests for idempotency key generation
        - Integration test: simulate timeout then retry
        - Tested against Stripe test mode with forced timeouts

        **Note:** This uses Stripe's built-in idempotency support. Keys expire after 24h
        per Stripe's docs, so we include date in the key to handle multi-day retries.""",
        state="closed",
        author_login="raj-patel",
        merged=True,
        merged_at=base - timedelta(days=55),
        created_at=base - timedelta(days=59),
        github_url=f"{DEMO_URL}/pull/47",
    )
    session.add(pr1)
    await session.flush()

    # Link PR to commits
    for commit_id in commit_ids[3:6]:
        prc = PullRequestCommit(pull_request_id=pr1.id, commit_id=commit_id)
        session.add(prc)

    pr2 = PullRequest(
        repository_id=repo_id,
        github_pr_number=62,
        title="Fix webhook idempotency to prevent duplicate fulfillment",
        body="""Fixes #124

        The retry logic added in #47 didn't account for webhook retries.
        When our fulfillment webhook fails (e.g., fulfillment service down),
        we retry the webhook but don't check if the order was already fulfilled.

        **Changes:**
        - Add idempotency check before triggering fulfillment
        - Store webhook delivery state in Redis with TTL
        - Skip fulfillment if already triggered within 24h window""",
        state="closed",
        author_login="maria-santos",
        merged=True,
        merged_at=base - timedelta(days=28),
        created_at=base - timedelta(days=31),
        github_url=f"{DEMO_URL}/pull/62",
    )
    session.add(pr2)
    await session.flush()

    for commit_id in commit_ids[6:7]:
        prc = PullRequestCommit(pull_request_id=pr2.id, commit_id=commit_id)
        session.add(prc)

    # ---- Comments ----
    comments_data = [
        (pr1.id, "pull_request", "senior-engineer", base - timedelta(days=58),
         "Good catch on the idempotency key. One question: why include the date in the key? "
         "If a payment takes more than 24h to resolve, we'll generate a different key and lose the dedup protection.",
         f"{DEMO_URL}/pull/47#pullrequestreview-111"),
        (pr1.id, "pull_request", "raj-patel", base - timedelta(days=58),
         "@senior-engineer Stripe's idempotency keys themselves expire after 24h per their docs "
         "(https://stripe.com/docs/api/idempotent_requests). Including the date means we never "
         "accidentally reuse a key after it's expired. Multi-day edge case is acceptable since "
         "payments that take >24h should be investigated manually anyway.",
         f"{DEMO_URL}/pull/47#pullrequestreview-112"),
        (pr1.id, "pull_request", "sarah-chen", base - timedelta(days=57),
         "LGTM. The DuplicateChargeError catch is important — tested locally with Stripe test mode "
         "and it correctly handles the 'already charged' case. Approving.",
         f"{DEMO_URL}/pull/47#pullrequestreview-113"),
        (issue1.id, "issue", "alice-ops", base - timedelta(days=61),
         "Confirmed 3 customer cases in the last hour. This is causing real revenue impact. "
         "Stripe is refunding the duplicate charges but it's a bad customer experience. "
         "Tagging @raj-patel since he owns the payment service.",
         f"{DEMO_URL}/issues/89#issuecomment-200"),
        (issue1.id, "issue", "raj-patel", base - timedelta(days=61),
         "Looking into this now. The problem is in retry.py around line 42-60. "
         "We're not using Stripe's idempotency keys, so retries always create new charges. "
         "Will have a fix up shortly.",
         f"{DEMO_URL}/issues/89#issuecomment-201"),
    ]

    for source_id, source_type, author, ts, body, url in comments_data:
        comment = Comment(
            repository_id=repo_id,
            source_type=source_type,
            source_id=source_id,
            author_login=author,
            body=body,
            created_at=ts,
            github_url=url,
        )
        session.add(comment)

    # ---- Relationships ----
    rel_data = [
        ("pull_request", pr1.id, "issue", issue1.id, "fixes", 0.95,
         "PR body: 'Fixes #89'"),
        ("pull_request", pr2.id, "issue", issue2.id, "fixes", 0.95,
         "PR body: 'Fixes #124'"),
        ("pull_request", pr2.id, "issue", issue1.id, "references", 0.7,
         "PR body references #89 as related"),
        ("issue", issue2.id, "issue", issue1.id, "references", 0.8,
         "Issue body: 'Related to: #89'"),
    ]

    for src_type, src_id, tgt_type, tgt_id, rel_type, conf, evidence in rel_data:
        rel = Relationship(
            repository_id=repo_id,
            source_type=src_type,
            source_id=src_id,
            target_type=tgt_type,
            target_id=tgt_id,
            relationship_type=rel_type,
            confidence=conf,
            evidence=evidence,
        )
        session.add(rel)

    # Commit modifies file relationships
    for commit_id in commit_ids[3:6]:
        rel = Relationship(
            repository_id=repo_id,
            source_type="commit",
            source_id=commit_id,
            target_type="file",
            target_id=file_ids["src/payments/retry.py"],
            relationship_type="modifies",
            confidence=1.0,
        )
        session.add(rel)

    await session.commit()
    return repo_id
