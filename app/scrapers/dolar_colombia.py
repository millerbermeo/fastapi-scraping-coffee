import logging
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.schemas.dolar import DolarColombiaResponse, DolarDay

logger = logging.getLogger(__name__)


class DolarColombiaScraper:
    source = "DOLAR-COLOMBIA"
    base_url = "https://www.dolar-colombia.com/"

    def fetch(self, date_str: Optional[str] = None) -> DolarColombiaResponse:
        result = DolarColombiaResponse()
        try:
            result.data = self._fetch_day(date_str)
            result.success = True
        except Exception as e:
            result.error = str(e)
            logger.error("DolarColombia scraper failed: %s", e)

        return result

    def _fetch_day(self, date_str: Optional[str]) -> DolarDay:
        url = self.base_url + (date_str if date_str else "")
        resp = httpx.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
            timeout=10.0,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        label = soup.select_one(".box__title").get_text(strip=True).split("-")[0].strip()

        rate_span = soup.select_one(".exchange-rate")
        raw_price = rate_span.get_text(strip=True)
        price = float(raw_price.replace(",", ""))

        classes = rate_span.get("class", [])
        if "exchange-rate_down" in classes:
            trend = "down"
        elif "exchange-rate_up" in classes:
            trend = "up"
        else:
            trend = "unchanged"

        written_el = soup.select_one(".exchange-rate__sub-text")
        price_written = written_el.get_text(strip=True) if written_el else ""

        summary_el = soup.select_one(".resume .text")
        summary = summary_el.get_text(strip=True) if summary_el else None

        date_input = soup.select_one(".form-choose-date input[name='fecha']")
        iso_date = date_input["value"] if date_input else (date_str or date.today().isoformat())

        return DolarDay(
            date=iso_date,
            label=label,
            price=price,
            price_formatted=raw_price,
            price_written=price_written,
            trend=trend,
            summary=summary,
            source_url=url,
        )
