from fastapi import APIRouter

from app.config import settings
from app.deps import invalidate_cache
from app.scrapers import SCRAPERS

router = APIRouter(tags=["health"])


@router.get("/health", summary="Estado de la API")
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "sources": list(SCRAPERS.keys()),
    }


@router.post("/cache/clear", summary="Limpiar cache")
async def clear_cache():
    invalidate_cache()
    return {"status": "cache cleared"}
