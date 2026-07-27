from app.scrapers.base import BaseScraper
from app.scrapers.fnc import FNCScraper
from app.scrapers.ice import ICEScraper
from app.scrapers.coocafisa import CoocafisaScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    "fnc": FNCScraper,
    "ice": ICEScraper,
    "coocafisa": CoocafisaScraper,
}

__all__ = ["SCRAPERS", "BaseScraper"]
