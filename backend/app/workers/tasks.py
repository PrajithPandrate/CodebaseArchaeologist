from .celery_app import celery_app
from ..services.repo_ingestion import run_ingestion


@celery_app.task(bind=True, name="ingest_repository", max_retries=1)
def ingest_repository(self, repo_id: str, github_token: str = None):
    """Background task to ingest a GitHub repository."""
    try:
        run_ingestion(repo_id, github_token)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
