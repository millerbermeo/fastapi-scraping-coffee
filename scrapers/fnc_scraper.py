import re
import logging
from typing import Optional

from playwright.sync_api import Page, sync_playwright

from models import MarketPrice

logger = logging.getLogger(__name__)


class FNCScraper:
    URL = "https://huila.federaciondecafeteros.org/precio-delcafe/"
    SOURCE = "FNC"
    LOAD_KG = 125

    def get_market_data(self) -> MarketPrice:
        result = MarketPrice(
            source=self.SOURCE,
            market="Café Colombiano - Precio Interno",
            page_name="Federación Nacional de Cafeteros - Precio del Café",
            page_url=self.URL,
            currency="COP",
            unit="COP",
        )
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.URL, wait_until="networkidle")
                page.wait_for_timeout(2000)

                self._click_all_price_items(page)

                self._extract_internal_price(page, result)
                self._extract_nyse_price(page, result)
                self._extract_trm(page, result)

                result.success = True
                browser.close()

        except Exception as e:
            result.error = str(e)
            logger.error("FNC scraper failed: %s", e)

        return result

    def _click_all_price_items(self, page: Page) -> None:
        items = page.locator(".e-n-menu-title").all()
        for item in items[:4]:
            try:
                item.click()
                page.wait_for_timeout(300)
            except Exception:
                pass

    def _extract_internal_price(self, page: Page, result: MarketPrice) -> None:
        title_el = page.locator(".e-n-menu-title-text").filter(
            has_text="Precio interno"
        ).first
        if not title_el:
            return

        raw = title_el.inner_text()
        price_num = self._parse_colombian_number(raw)
        if price_num is not None:
            result.internal_price = price_num
            result.price = price_num
            result.price_per_kg = round(price_num / self.LOAD_KG, 2)

        date = self._extract_date_from_content(page, "Precio interno")
        if date:
            result.date = date

    def _extract_nyse_price(self, page: Page, result: MarketPrice) -> None:
        title_el = page.locator(".e-n-menu-title-text").filter(
            has_text="Bolsa de NY"
        ).first
        if not title_el:
            return

        raw = title_el.inner_text()
        price_num = self._parse_colombian_number(raw)
        if price_num is not None:
            result.nyse_price = price_num

        date = self._extract_date_from_content(page, "Bolsa de NY")
        if date and not result.date:
            result.date = date

    def _extract_trm(self, page: Page, result: MarketPrice) -> None:
        title_el = page.locator(".e-n-menu-title-text").filter(
            has_text="Tasa de cambio"
        ).first
        if not title_el:
            return

        raw = title_el.inner_text()
        trm_num = self._parse_colombian_number(raw)
        if trm_num is not None:
            result.trm = trm_num

        date = self._extract_date_from_content(page, "Tasa de cambio")
        if date and not result.date:
            result.date = date

    def _extract_date_from_content(self, page: Page, label: str) -> Optional[str]:
        try:
            content = page.locator("[id^=e-n-menu-content-]").filter(
                has_text=label
            ).first
            text = content.inner_text()
            match = re.search(r"Fecha:\s*(\d{4}-\d{2}-\d{2})", text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def _parse_colombian_number(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.strip()
        text = text.replace("$", "").replace("USD", "").strip()

        if "," in text and text.rindex(",") > text.rindex(".") if "." in text else False:
            parts = text.rsplit(",", 1)
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1]
            cleaned = f"{integer_part}.{decimal_part}"
        else:
            cleaned = text.replace(".", "").replace(",", ".")

        match = re.search(r"-?[\d.]+", cleaned.replace(",", "."))
        if not match:
            return None
        try:
            return float(match.group())
        except ValueError:
            return None
