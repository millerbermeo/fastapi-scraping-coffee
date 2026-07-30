import logging
from typing import Optional

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

from app.scrapers.base import BaseScraper
from app.schemas.market import MarketPrice

logger = logging.getLogger(__name__)


class CoocafisaScraper(BaseScraper):
    source = "COOCAFISA"
    url = "https://coocafisa.com/"

    def get_market_data(self) -> MarketPrice:
        result = MarketPrice(
            source=self.source,
            market="Cooperativa de Caficultores de Salgar",
            page_name="Coocafisa - Precio del Café",
            page_url=self.url,
            currency="COP",
            unit="COP",
        )
        try:
            resp = curl_requests.get(
                self.url,
                impersonate="chrome120",
                timeout=10,
                allow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            result.prices = self._extract_prices(soup)
            for p in result.prices:
                if p["price"] > 0:
                    result.price = p["price"]
                    break
            # La página no publica fecha del precio, solo el valor vigente.
            result.updated_at = self._now_utc()
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error("Coocafisa scraper failed: %s", e)

        return result

    def _extract_prices(self, soup: BeautifulSoup) -> list[dict]:
        slides = soup.select(".bt_bb_content_slider_item .bt_bb_text")
        seen: set[str] = set()
        prices: list[dict] = []

        for slide in slides:
            lines = [line.strip() for line in slide.get_text().split("\n") if line.strip()]
            if len(lines) < 2 or not lines[0].startswith("Factor"):
                continue

            factor_name = lines[0]
            raw_price = lines[1]

            if factor_name in seen:
                continue
            seen.add(factor_name)

            parsed = self._parse_price(raw_price)
            if parsed is not None:
                prices.append({"factor": factor_name, "price": parsed, "raw": raw_price})

        return prices

    def _parse_price(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.replace("$", "").replace("*", "").strip()
        text = text.replace(".", "").replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None
