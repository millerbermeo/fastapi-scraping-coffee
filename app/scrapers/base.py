from abc import ABC, abstractmethod

from app.schemas.market import MarketPrice


class BaseScraper(ABC):
    source: str
    url: str

    @abstractmethod
    def get_market_data(self) -> MarketPrice: ...
