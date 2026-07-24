from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class MarketPrice:
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

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}
