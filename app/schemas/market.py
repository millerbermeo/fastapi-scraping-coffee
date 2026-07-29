from typing import Optional

from pydantic import BaseModel


class MarketPrice(BaseModel):
    source: str
    market: str
    page_name: str = ""
    page_url: str = ""
    success: bool = False
    error: Optional[str] = None

    price: Optional[float] = None
    currency: str = "USD"
    unit: str = ""
    trm: Optional[float] = None
    date: Optional[str] = None
    updated_at: Optional[str] = None

    internal_price: Optional[float] = None
    price_per_kg: Optional[float] = None
    nyse_price: Optional[float] = None
    prices: Optional[list[dict]] = None

    mecic: Optional[float] = None
    pdf_url: Optional[str] = None
