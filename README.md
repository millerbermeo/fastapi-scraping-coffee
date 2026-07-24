# Market Scraper - Precio del Café

Extrae el precio del café desde dos fuentes oficiales usando Playwright.

## Fuentes

- **FNC** - Federación Nacional de Cafeteros de Colombia (precio interno, Bolsa NY, TRM)
- **ICE** - Intercontinental Exchange (Coffee C Futures front month)

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso

```bash
python main.py
```

## Estructura

```
market_scraper/
├── scrapers/
│   ├── fnc_scraper.py   # Scraper FNC (WordPress + Elementor)
│   └── ice_scraper.py   # Scraper ICE (API REST + DOM fallback)
├── models.py            # Dataclass MarketPrice
├── main.py              # Orquestador
├── requirements.txt
└── README.md
```
