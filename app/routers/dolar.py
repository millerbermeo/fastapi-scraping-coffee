from datetime import date as date_cls
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.deps import get_cached
from app.scrapers.dolar_colombia import DolarColombiaScraper
from app.schemas.dolar import DolarColombiaResponse

router = APIRouter(prefix="/dolar-colombia", tags=["dolar"])


@router.get(
    "",
    response_model=DolarColombiaResponse,
    response_model_exclude_none=True,
    summary="Precio del dólar (hoy, o de una fecha específica)",
)
async def get_dolar_colombia(
    fecha: Optional[str] = Query(
        None, description="Fecha AAAA-MM-DD. Si se omite, trae el precio de hoy."
    )
):
    if fecha is not None:
        try:
            date_cls.fromisoformat(fecha)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Formato de fecha inválido, use AAAA-MM-DD"
            )

    scraper = DolarColombiaScraper()
    cache_key = f"dolar:{fecha or date_cls.today().isoformat()}"
    return await get_cached(cache_key, scraper.fetch, fecha)
