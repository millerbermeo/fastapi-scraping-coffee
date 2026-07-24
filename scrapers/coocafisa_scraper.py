import re
import logging
from typing import Optional
from dataclasses import dataclass, asdict

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


@dataclass
class CoocafisaPrice:
    factor: str
    price: float
    raw: str


class CoocafisaScraper:
    URL = "https://coocafisa.com/"
    SOURCE = "COOCAFISA"

    PAGE_NAME = "Coocafisa - Precio del Café"

    def get_market_data(self) -> dict:
        result = {
            "source": self.SOURCE,
            "market": "Cooperativa de Caficultores de Salgar",
            "page_name": self.PAGE_NAME,
            "page_url": self.URL,
            "success": False,
            "error": None,
            "date": None,
            "prices": [],
        }
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.URL, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(5000)

                slides = page.query_selector_all(".bt_bb_content_slider_item .bt_bb_text")
                seen = set()
                prices = []
                for slide in slides:
                    text = slide.inner_text().strip()
                    if "Factor" not in text:
                        continue
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) < 2:
                        continue
                    factor_name = lines[0]
                    raw_price = lines[1]

                    key = (factor_name, raw_price)
                    if key in seen:
                        continue
                    seen.add(key)

                    parsed = self._parse_price(raw_price)
                    if parsed is not None:
                        prices.append(CoocafisaPrice(
                            factor=factor_name,
                            price=parsed,
                            raw=raw_price,
                        ))

                result["prices"] = [asdict(p) for p in prices]

                result["date"] = self._extract_date(page)
                result["success"] = True
                browser.close()

        except Exception as e:
            result["error"] = str(e)
            logger.error("Coocafisa scraper failed: %s", e)

        return result

    def _extract_date(self, page) -> Optional[str]:
        try:
            el = page.query_selector("#fecha-actual")
            if el:
                return el.inner_text().strip()
        except Exception:
            pass
        return None

    def _parse_price(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.replace("$", "").replace("*", "").strip()
        text = text.replace(".", "")
        text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None
