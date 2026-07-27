import asyncio

from fastapi import APIRouter, HTTPException

from app.deps import get_price
from app.scrapers import SCRAPERS
from app.schemas.market import MarketPrice

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get(
    "",
    response_model=list[MarketPrice],
    response_model_exclude_none=True,
    summary="Precio de todas las fuentes",
)
async def get_all_prices():
    results = await asyncio.gather(*(get_price(cls) for cls in SCRAPERS.values()))
    return results


@router.get(
    "/{source}",
    response_model=MarketPrice,
    response_model_exclude_none=True,
    summary="Precio de una fuente específica",
)
async def get_price_by_source(source: str):
    key = source.lower()
    if key not in SCRAPERS:
        available = ", ".join(SCRAPERS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Fuente '{source}' no encontrada. Disponibles: {available}",
        )
    return await get_price(SCRAPERS[key])
