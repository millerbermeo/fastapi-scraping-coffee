# Coffee Price API

API REST que obtiene precios del café en tiempo real desde múltiples fuentes usando Playwright.

## Fuentes

- **FNC** - Federación Nacional de Cafeteros de Colombia (precio interno, Bolsa NY, TRM)
- **ICE** - Intercontinental Exchange (Coffee C Futures front month)
- **Coocafisa** - Cooperativa de Caficultores de Salgar (múltiples factores)

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso

```bash
python run.py
```

La API estará disponible en `http://localhost:8000`

## Docker

Requisitos: Docker Engine 20.10+ y Docker Compose v2 (`docker compose`, no `docker-compose`).
Probado contra la configuración estándar de Ubuntu 20.04 LTS y Ubuntu 24.04 LTS.

### Preparar variables de entorno

```bash
cp .env.example .env
```

`.env` es obligatorio: `docker-compose.yml` lo declara en `env_file` y lo usa para
interpolar el puerto. Ninguna configuración está hardcodeada en la imagen.

### Construcción

```bash
docker compose build
```

### Ejecución

```bash
docker compose up
```

API disponible en `http://localhost:8000` (o el `APP_PORT` definido en `.env`).
Documentación interactiva en `http://localhost:8000/docs`.

### Modo desarrollo

```bash
docker compose up --build
```

El código se monta como volumen de solo lectura (`./app`, `./run.py`). Con
`UVICORN_RELOAD=1` en `.env`, uvicorn recarga automáticamente al guardar un archivo.
Para ejecutar igual que en producción, deja `UVICORN_RELOAD=` vacío.

### Detener

```bash
docker compose down
```

### Reconstrucción completa

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Variables de entorno de infraestructura

| Variable | Default | Descripción |
|----------|---------|-------------|
| `APP_HOST` | `0.0.0.0` | Interfaz de escucha de uvicorn |
| `APP_PORT` | `8000` | Puerto del contenedor y del host |
| `UVICORN_RELOAD` | `1` | Valor no vacío activa `--reload` |

### Notas de la imagen

- Multi-stage sobre `python:3.12-slim-bookworm`; el runtime no incluye pip cache ni herramientas de compilación.
- Se ejecuta como usuario no root (`appuser`, uid 1001).
- Incluye el paquete `tzdata` porque `app/scrapers/ice.py` usa `ZoneInfo("America/New_York")` y las imágenes slim de Debian no traen la base de datos IANA.
- Incluye `uvicorn[standard]` (uvloop, httptools, watchfiles) para rendimiento y para soportar `--reload`.
- `HEALTHCHECK` consulta `/health` con la stdlib; no requiere `curl`.
- No se declaran servicios de base de datos, cache ni broker: la app es stateless y su cache es en memoria (`cachetools.TTLCache`).

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/prices/` | Precios de todas las fuentes |
| GET | `/prices/{source}` | Precio de una fuente (`fnc`, `ice`, `coocafisa`) |
| GET | `/health` | Estado de la API |
| POST | `/cache/clear` | Limpiar cache |

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `COFFEE_DEBUG` | `false` | Modo debug (reload automático) |
| `COFFEE_CACHE_TTL_SECONDS` | `300` | TTL del cache en segundos |
| `COFFEE_SCRAPER_HEADLESS` | `true` | Chromium headless |

## Estructura

```
fastapi-scraping-coffee/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings (pydantic-settings)
│   ├── deps.py              # Cache + dependencies
│   ├── routers/
│   │   ├── prices.py        # GET /prices
│   │   └── health.py        # GET /health
│   ├── schemas/
│   │   └── market.py        # Pydantic models
│   └── scrapers/
│       ├── base.py          # BaseScraper (ABC)
│       ├── fnc.py           # Scraper FNC
│       ├── ice.py           # Scraper ICE
│       └── coocafisa.py     # Scraper Coocafisa
├── run.py                   # Entry point
├── requirements.txt
└── README.md
```

## Agregar una nueva fuente

1. Crear `app/scrapers/nueva_fuente.py` heredando de `BaseScraper`
2. Implementar `get_market_data() -> MarketPrice`
3. Registrar en `app/scrapers/__init__.py`

```python
from app.scrapers.base import BaseScraper
from app.schemas.market import MarketPrice

class NuevaFuenteScraper(BaseScraper):
    source = "NUEVA_FUENTE"
    url = "https://..."

    def get_market_data(self) -> MarketPrice:
        ...
```
