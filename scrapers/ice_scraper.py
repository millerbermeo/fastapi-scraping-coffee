import json
import logging
from typing import Any, Optional

from playwright.sync_api import sync_playwright

from models import MarketPrice

logger = logging.getLogger(__name__)


class ICEScraper:
    URL = "https://www.ice.com/products/15/Coffee-C-Futures/data"
    SOURCE = "ICE"

    def get_market_data(self) -> MarketPrice:
        result = MarketPrice(
            source=self.SOURCE,
            market="Coffee C Futures",
            page_name="ICE - Coffee C Futures Data",
            page_url=self.URL,
            currency="USD",
            unit="centavos USD/libra",
        )
        captured_data: dict[str, Any] = {}

        def capture_response(response) -> None:
            if "contract-data" in response.url:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        captured_data["contracts"] = data
                except Exception:
                    pass

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = context.new_page()
                page.on("response", capture_response)

                page.goto(self.URL, wait_until="networkidle")
                page.wait_for_timeout(3000)

                if captured_data.get("contracts"):
                    self._parse_api_data(captured_data["contracts"], result)
                else:
                    self._parse_dom_data(page, result)

                result.success = True
                browser.close()

        except Exception as e:
            result.error = str(e)
            logger.error("ICE scraper failed: %s", e)

        return result

    def _parse_api_data(self, contracts: list[dict], result: MarketPrice) -> None:
        active_contract = self._find_active_contract(contracts)
        if not active_contract:
            return

        last_price = active_contract.get("lastPrice")
        if last_price is not None:
            result.price = float(last_price)

        change = active_contract.get("change")
        if change is not None:
            result.variation = round(float(change), 2)

        market_strip = active_contract.get("marketStrip", "")
        if market_strip:
            result.contract = market_strip

        volume = active_contract.get("volume")
        if volume is not None:
            result.volume = int(volume)

        last_time = active_contract.get("lastTime", "")
        if last_time:
            result.updated_at = last_time

    def _find_active_contract(self, contracts: list[dict]) -> Optional[dict]:
        if not contracts:
            return None
        sorted_contracts = sorted(
            contracts,
            key=lambda c: c.get("volume", 0) or 0,
            reverse=True,
        )
        return sorted_contracts[0]

    def _parse_dom_data(self, page, result: MarketPrice) -> None:
        try:
            rows = page.locator("table.table-data tbody tr").all()
            for row in rows:
                cells = row.locator("td").all()
                if len(cells) >= 4:
                    raw_price = cells[1].inner_text().strip()
                    try:
                        result.price = float(raw_price)
                    except ValueError:
                        pass

                    raw_change = cells[3].inner_text().strip()
                    try:
                        result.variation = float(raw_change)
                    except ValueError:
                        pass

                    result.contract = cells[0].inner_text().strip()
                    break
        except Exception as e:
            logger.warning("DOM fallback failed: %s", e)
