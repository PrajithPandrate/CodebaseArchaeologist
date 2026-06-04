from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.hotspot_analysis import get_hotspots, get_dashboard_stats

router = APIRouter(prefix="/api/repositories/{repo_id}", tags=["hotspots"])


@router.get("/hotspots")
async def get_hotspot_analysis(repo_id: str, session: AsyncSession = Depends(get_session)):
    hotspots = await get_hotspots(session, repo_id)
    return {"hotspots": hotspots}


@router.get("/stats")
async def get_stats(repo_id: str, session: AsyncSession = Depends(get_session)):
    stats = await get_dashboard_stats(session, repo_id)
    return stats
