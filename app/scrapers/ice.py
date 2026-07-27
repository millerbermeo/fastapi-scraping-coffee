import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.scrapers.base import BaseScraper
from app.schemas.market import MarketPrice

logger = logging.getLogger(__name__)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/KC=F"
YAHOO_HOME = "https://finance.yahoo.com/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class ICEScraper(BaseScraper):
    source = "ICE"
    url = "https://www.ice.com/products/15/Coffee-C-Futures/data"

    def get_market_data(self) -> MarketPrice:
        result = MarketPrice(
            source=self.source,
            market="Coffee C Futures",
            page_name="ICE - Coffee C Futures Data",
            page_url=self.url,
            currency="USD",
            unit="centavos USD/libra",
        )
        try:
            with httpx.Client() as client:
                client.get(YAHOO_HOME, headers={"User-Agent": UA})

                resp = client.get(
                    YAHOO_CHART_URL,
                    params={"interval": "1d", "range": "1d"},
                    headers={
                        "User-Agent": UA,
                        "Accept": "application/json",
                        "Referer": "https://finance.yahoo.com/quote/KC=F/",
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()

                meta = data["chart"]["result"][0]["meta"]
                quote = data["chart"]["result"][0]["indicators"]["quote"][0]

                result.price = round(meta["regularMarketPrice"], 2)
                result.volume = meta.get("regularMarketVolume")

                prev_close = meta.get("chartPreviousClose")
                current = meta["regularMarketPrice"]
                if prev_close and prev_close > 0:
                    result.variation = round(((current - prev_close) / prev_close) * 100, 2)
                    result.previous_close = round(prev_close, 2)

                contract = meta.get("shortName")
                if contract:
                    result.contract = contract

                if meta.get("regularMarketDayHigh") is not None:
                    result.day_high = round(meta["regularMarketDayHigh"], 2)
                if meta.get("regularMarketDayLow") is not None:
                    result.day_low = round(meta["regularMarketDayLow"], 2)
                if meta.get("regularMarketOpen") is not None:
                    result.day_open = round(meta["regularMarketOpen"], 2)
                if meta.get("fiftyTwoWeekHigh") is not None:
                    result.fifty_two_week_high = round(meta["fiftyTwoWeekHigh"], 2)
                if meta.get("fiftyTwoWeekLow") is not None:
                    result.fifty_two_week_low = round(meta["fiftyTwoWeekLow"], 2)
                result.exchange_name = meta.get("exchangeName")

                ts = meta.get("regularMarketTime")
                if ts:
                    dt = datetime.fromtimestamp(ts, tz=ZoneInfo("America/New_York"))
                    result.date = dt.strftime("%Y-%m-%d %I:%M %p")

                result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error("ICE scraper failed: %s", e)

        return result
