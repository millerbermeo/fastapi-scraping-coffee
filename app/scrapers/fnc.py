import re
import logging
import time
from typing import Optional

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from curl_cffi.requests import exceptions as curl_exc

from app.scrapers.base import BaseScraper
from app.schemas.market import MarketPrice

logger = logging.getLogger(__name__)


class FNCScraper(BaseScraper):
    source = "FNC"
    url = "https://huila.federaciondecafeteros.org/precio-delcafe/"
    LOAD_KG = 125
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def _request_with_retry(self) -> curl_requests.Response:
        last_exc = None
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = curl_requests.get(
                    self.url,
                    impersonate="chrome120",
                    timeout=20,
                    allow_redirects=True,
                )
                resp.raise_for_status()
                return resp
            except (curl_exc.ConnectionError, curl_exc.Timeout) as e:
                last_exc = e
                logger.warning("FNC request attempt %d/%d failed: %s", attempt + 1, self.MAX_RETRIES, e)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))
            except curl_exc.HTTPError as e:
                if e.response is not None and e.response.status_code >= 500 and attempt < self.MAX_RETRIES - 1:
                    last_exc = e
                    logger.warning("FNC request attempt %d/%d failed (HTTP %d)", attempt + 1, self.MAX_RETRIES, e.response.status_code)
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))
                else:
                    raise
        raise last_exc

    def get_market_data(self) -> MarketPrice:
        result = MarketPrice(
            source=self.source,
            market="Café Colombiano - Precio Interno",
            page_name="Federación Nacional de Cafeteros - Precio del Café",
            page_url=self.url,
            currency="COP",
            unit="COP",
        )
        try:
            resp = self._request_with_retry()
            soup = BeautifulSoup(resp.text, "html.parser")

            self._extract_internal_price(soup, result)
            self._extract_nyse_price(soup, result)
            self._extract_trm(soup, result)
            self._extract_mecic(soup, result)
            self._extract_pdf_url(soup, result)

            result.updated_at = self._now_utc()
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error("FNC scraper failed: %s", e)

        return result

    def _extract_internal_price(self, soup: BeautifulSoup, result: MarketPrice) -> None:
        title = self._find_menu_text(soup, "Precio interno")
        if not title:
            return

        price_num = self._parse_colombian_number(title)
        if price_num is not None:
            result.internal_price = price_num
            result.price = price_num
            result.price_per_kg = round(price_num / self.LOAD_KG, 2)

        date = self._find_date_near(soup, "Precio interno")
        if date:
            result.date = date

    def _extract_nyse_price(self, soup: BeautifulSoup, result: MarketPrice) -> None:
        title = self._find_menu_text(soup, "Bolsa de NY")
        if not title:
            return

        price_num = self._parse_colombian_number(title)
        if price_num is not None:
            result.nyse_price = price_num

        date = self._find_date_near(soup, "Bolsa de NY")
        if date and not result.date:
            result.date = date

    def _extract_trm(self, soup: BeautifulSoup, result: MarketPrice) -> None:
        title = self._find_menu_text(soup, "Tasa de cambio")
        if not title:
            return

        trm_num = self._parse_colombian_number(title)
        if trm_num is not None:
            result.trm = trm_num

        date = self._find_date_near(soup, "Tasa de cambio")
        if date and not result.date:
            result.date = date

    def _extract_mecic(self, soup: BeautifulSoup, result: MarketPrice) -> None:
        title = self._find_menu_text(soup, "MeCIC")
        if not title:
            return

        mecic_num = self._parse_colombian_number(title)
        if mecic_num is not None:
            result.mecic = mecic_num

    def _extract_pdf_url(self, soup: BeautifulSoup, result: MarketPrice) -> None:
        link = soup.find("a", href=re.compile(r"\.pdf$", re.I))
        if link:
            result.pdf_url = link.get("href")

    def _find_menu_text(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        el = soup.find(class_="e-n-menu-title-text", string=re.compile(label, re.I))
        return el.get_text(strip=True) if el else None

    def _find_date_near(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        container = soup.find(id=re.compile(r"^e-n-menu-content-"))
        if container and label.lower() in container.get_text().lower():
            match = re.search(r"Fecha:\s*(\d{4}-\d{2}-\d{2})", container.get_text())
            if match:
                return match.group(1)
        return None

    def _parse_colombian_number(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.strip().replace("$", "").replace("USD", "").strip()

        if "," in text and text.rindex(",") > text.rindex(".") if "." in text else False:
            parts = text.rsplit(",", 1)
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1]
            cleaned = f"{integer_part}.{decimal_part}"
        else:
            cleaned = text.replace(".", "").replace(",", ".")

        match = re.search(r"-?[\d.]+", cleaned)
        if not match:
            return None
        try:
            return float(match.group())
        except ValueError:
            return None
