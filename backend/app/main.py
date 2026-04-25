from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import create_db_and_tables
from .api import repositories, files, ask, timeline, graph, hotspots

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Codebase Archaeologist API",
    description="AI-powered code history investigation tool",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repositories.router)
app.include_router(files.router)
app.include_router(ask.router)
app.include_router(timeline.router)
app.include_router(graph.router)
app.include_router(hotspots.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "codebase-archaeologist"}


@app.get("/api/demo/seed")
async def seed_demo():
    """Triggers demo data seeding for showcase purposes."""
    from .demo.seed import seed_demo_data
    from .database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        repo_id = await seed_demo_data(session)
    return {"repository_id": repo_id, "status": "seeded"}
