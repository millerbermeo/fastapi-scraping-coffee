from typing import Optional

from pydantic import BaseModel


class DolarDay(BaseModel):
    date: str
    label: str
    price: float
    price_formatted: str
    price_written: str
    trend: Optional[str] = None
    summary: Optional[str] = None
    source_url: str


class DolarColombiaResponse(BaseModel):
    source: str = "DOLAR-COLOMBIA"
    currency_pair: str = "USD/COP"
    success: bool = False
    error: Optional[str] = None

    data: Optional[DolarDay] = None
