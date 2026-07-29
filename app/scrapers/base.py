from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.schemas.market import MarketPrice


class BaseScraper(ABC):
    source: str
    url: str

    @abstractmethod
    def get_market_data(self) -> MarketPrice: ...

    @staticmethod
    def _now_utc() -> str:
        """Momento del scrape, UTC ISO 8601. No es la fecha de publicación del precio."""
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
