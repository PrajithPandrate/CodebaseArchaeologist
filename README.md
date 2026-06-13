# Codebase Archaeologist

> Ask why code exists, not just what it does.

An AI-powered developer tool that analyzes GitHub repositories and answers questions like:
- *"Why does this retry logic exist?"*
- *"Who added this logic and what issue/PR caused it?"*
- *"What changed around this file before a bug was fixed?"*
- *"Which commits introduced the current behavior?"*

Every answer is **evidence-linked** — backed by real commits, pull requests, issues, and code review discussions. No hallucination, no guessing.

---

## Features

| Feature | Description |
|---------|-------------|
| **Code History Investigation** | Trace any function or file back to the PRs and issues that introduced it |
| **Hybrid Retrieval** | Semantic search + keyword + graph expansion over embeddings, commit messages, and metadata |
| **Evidence Citations** | Every AI answer includes numbered citations `[1]`, `[2]` linked to source artifacts |
| **Timeline View** | Chronological view of commits, PR merges, issue opens/closes |
| **Knowledge Graph** | Interactive React Flow graph of relationships (file → commit → PR → issue) |
| **Code Hotspots** | Files ranked by churn × author concentration as risk indicators |
| **Demo Mode** | One-click seeded dataset: payment service with retry logic history |
| **Secret Redaction** | API keys, tokens, and passwords scrubbed before embedding |
| **LLM-Agnostic** | Pluggable: Anthropic Claude, OpenAI GPT, or no LLM (keyword-only mode) |

---

## Architecture

```
┌────────────────────────────────────────────────┐
│                  Frontend (Next.js)              │
│   Landing │ Import │ Dashboard │ Files │ Ask    │
│   Timeline │ Graph │ Evidence Drawer │ Settings │
└───────────────────┬────────────────────────────┘
                    │ REST API
┌───────────────────▼────────────────────────────┐
│              Backend (FastAPI + Python)          │
│                                                  │
│  ┌─────────────┐  ┌──────────────────────────┐ │
│  │ Ingestion   │  │ Query Pipeline           │ │
│  │ - Clone     │  │ - Hybrid retrieval       │ │
│  │ - Chunk     │  │ - Re-ranking             │ │
│  │ - Git log   │  │ - Graph expansion        │ │
│  │ - GitHub API│  │ - LLM answer generation  │ │
│  └──────┬──────┘  └──────────────────────────┘ │
│         │                                        │
│  Celery Worker (background jobs)                 │
└──────┬──────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────┐
│  PostgreSQL + pgvector │ Redis                   │
│  - code_chunks (embeddings)                      │
│  - commits, pull_requests, issues, comments      │
│  - relationships (graph edges)                   │
└─────────────────────────────────────────────────┘
```

---

## Tech Stack

**Frontend**
- Next.js 15 + TypeScript
- Tailwind CSS + shadcn/ui components
- TanStack Query (React Query v5)
- Monaco Editor (code viewer with line numbers)
- React Flow (interactive knowledge graph)
- Recharts (dashboard analytics)

**Backend**
- FastAPI + Python 3.12
- SQLModel + SQLAlchemy + Alembic
- PostgreSQL 16 + pgvector
- Celery + Redis (background ingestion)
- GitPython (git operations)
- GitHub REST API (PRs, issues, comments)
- Anthropic Claude / OpenAI (LLM + embeddings)

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- (Optional) GitHub token for higher API rate limits
- (Optional) Anthropic API key for AI answers

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/codebase-archaeologist
cd codebase-archaeologist
cp .env.example backend/.env
# Edit backend/.env with your API keys
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)
- Celery worker
- Next.js frontend (port 3000)

### 3. Open the app

Visit [http://localhost:3000](http://localhost:3000)

### 4. Try the demo (no GitHub token needed)

Click **"Try the Demo"** on the import page, or:

```bash
curl http://localhost:8000/api/demo/seed
```

Then ask: *"Why was this retry logic added?"*

---

## Local Development (without Docker)

```bash
# Backend
make install-backend
cd backend
cp ../.env.example .env  # edit as needed
uvicorn app.main:app --reload --port 8000

# Worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Frontend (separate terminal)
make install-frontend
cd frontend
npm run dev

# Database migrations
cd backend && alembic upgrade head
```

---

## How Retrieval Works

For each question, the system runs **hybrid retrieval**:

```
final_score =
  0.45 × semantic_similarity   (pgvector cosine distance)
  0.20 × keyword_match_score   (TF-IDF-style over snippet)
  0.20 × graph_proximity       (hops from selected file/function)
  0.10 × source_quality        (PR merged > issue > commit > code)
  0.05 × recency               (decay over 5 years)
```

**Source quality scores:**
| Source | Score |
|--------|-------|
| Merged PR | 1.0 |
| Issue closed by PR | 0.9 |
| Commit message | 0.75 |
| Review comment | 0.7 |
| Code chunk | 0.65 |
| General docs | 0.6 |

---

## Database Schema Overview

```
repositories → ingestion_jobs
             → files → code_chunks (embedding vector)
             → commits → commit_file_changes
             → pull_requests → pull_request_commits
             → issues
             → comments (embedding vector)
             → relationships (source_type/id → target_type/id)
             → questions → answer_evidence
```

---

## Example Questions

- `"Why does this retry logic exist?"`
- `"What changed before the payment bug was fixed?"`
- `"Who understands the auth module best?"`
- `"Why was this caching layer added?"`
- `"Which PR introduced this behavior?"`
- `"Find all issues related to this file"`

---

## Configuration

Set in `backend/.env`:

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `anthropic` or `openai` or `none` |
| `ANTHROPIC_API_KEY` | For Claude answers + Voyage embeddings |
| `OPENAI_API_KEY` | Alternative LLM + `text-embedding-3-small` |
| `GITHUB_TOKEN` | Optional: raises API rate limits (5000 req/hr vs 60) |
| `EMBEDDING_PROVIDER` | `anthropic` (Voyage) or `openai` |

---

## Testing

```bash
# Backend unit tests
cd backend && pytest -v

# Covers:
# - Code chunking (Python, TypeScript)
# - Retrieval re-ranking
# - Secret redaction
# - GitHub metadata parsing
# - Answer citation format
```

---

## Resume Bullets

1. Built **Codebase Archaeologist**, an AI developer tool that indexes code, commits, pull requests, issues, and comments to answer *"why does this code exist?"* with source-linked evidence.
2. Designed a **hybrid retrieval pipeline** over pgvector embeddings, keyword search, and graph relationships to trace functions/files back to historical PRs, commits, and issue discussions.
3. Implemented repository ingestion, semantic code chunking, GitHub metadata sync, timeline generation, and an interactive React Flow **knowledge graph** for code-history exploration.

---

## Future Improvements

- Tree-sitter for precise AST-level code chunking
- GitHub webhook integration for live index updates
- Blame-aware retrieval (git blame per line range)
- Slack/Jira integration for additional context
- Local LLM support (Ollama/llama.cpp)
- Repository comparison mode
- CI/CD integration for change-impact analysis
