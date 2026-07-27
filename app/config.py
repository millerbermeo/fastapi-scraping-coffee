from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "COFFEE_"}

    app_name: str = "Coffee Price API"
    app_version: str = "1.0.0"
    debug: bool = False

    cache_ttl_seconds: int = 300
    scraper_timeout_ms: int = 30000
    scraper_headless: bool = True


settings = Settings()
