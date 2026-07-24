import logging

from fastapi import FastAPI

from scrapers.fnc_scraper import FNCScraper
from scrapers.ice_scraper import ICEScraper
from scrapers.coocafisa_scraper import CoocafisaScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Coffee Price API",
    description="Precio del café desde FNC, Coocafisa (Colombia) e ICE (Coffee C Futures)",
    version="1.0.0",
)


@app.get("/")
def get_coffee_prices():
    fnc = FNCScraper().get_market_data()
    ice = ICEScraper().get_market_data()
    coocafisa = CoocafisaScraper().get_market_data()
    return {
        "fnc": fnc.to_dict(),
        "ice": ice.to_dict(),
        "coocafisa": coocafisa,
    }
