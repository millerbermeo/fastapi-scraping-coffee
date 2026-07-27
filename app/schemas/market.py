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
    variation: Optional[float] = None
    trm: Optional[float] = None
    date: Optional[str] = None
    updated_at: Optional[str] = None

    internal_price: Optional[float] = None
    price_per_kg: Optional[float] = None
    nyse_price: Optional[float] = None
    volume: Optional[int] = None
    contract: Optional[str] = None
    prices: Optional[list[dict]] = None

    day_high: Optional[float] = None
    day_low: Optional[float] = None
    day_open: Optional[float] = None
    previous_close: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    exchange_name: Optional[str] = None

    mecic: Optional[float] = None
    pdf_url: Optional[str] = None
