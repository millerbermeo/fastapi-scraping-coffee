import asyncio
import logging
from functools import lru_cache

from cachetools import TTLCache

from app.config import settings
from app.schemas.market import MarketPrice

logger = logging.getLogger(__name__)

_cache: TTLCache = TTLCache(maxsize=16, ttl=settings.cache_ttl_seconds)


def _run_scraper_sync(scraper_cls) -> MarketPrice:
    scraper = scraper_cls()
    return scraper.get_market_data()


async def get_price(scraper_cls) -> MarketPrice:
    key = scraper_cls.source
    cached = _cache.get(key)
    if cached is not None:
        logger.info("Cache hit for %s", key)
        return cached

    logger.info("Fetching %s (no cache)", key)
    result = await asyncio.to_thread(_run_scraper_sync, scraper_cls)
    _cache[key] = result
    return result


def invalidate_cache() -> None:
    _cache.clear()
