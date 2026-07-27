from fastapi import APIRouter, HTTPException

from app.deps import get_price
from app.scrapers import SCRAPERS
from app.schemas.market import MarketPrice, PrecioCafe

router = APIRouter(prefix="/prices", tags=["prices"])


def _to_precio(data: MarketPrice) -> PrecioCafe:
    return PrecioCafe(
        fuente=data.source,
        mercado=data.market,
        precio=data.price,
        moneda=data.currency,
        fecha=data.date,
    )


@router.get("/{source}", response_model=PrecioCafe, summary="Precio de una fuente específica")
async def get_price_by_source(source: str):
    key = source.lower()
    if key not in SCRAPERS:
        available = ", ".join(SCRAPERS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Fuente '{source}' no encontrada. Disponibles: {available}",
        )
    data = await get_price(SCRAPERS[key])
    return _to_precio(data)
