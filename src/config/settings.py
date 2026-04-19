from __future__ import annotations
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8', 'case_sensitive': False}

    # SWAPI
    swapi_base_url: str = Field(default='https://swapi.dev/api')
    http_timeout_seconds: float = Field(default=30.0)
    http_max_retries: int = Field(default=3)

    # Wookieepedia scraping
    wookieepedia_base_url: str = Field(default='https://starwars.fandom.com/wiki')
    scraping_concurrency: int = Field(default=5)
    scraping_headless: bool = Field(default=True)
    scraping_max_retries: int = Field(default=2)
    scraping_page_timeout_ms: int = Field(default=20_000)
    scraping_selector_timeout_ms: int = Field(default=8_000)

    # StarWars.com Databank scraping
    starwars_databank_base_url: str = Field(default='https://www.starwars.com/databank')
    databank_scraping_enabled: bool = Field(default=True)

    # Output
    output_path: Path = Field(default=Path('output/characters.json'))
    log_level: str = Field(default='INFO')

settings = Settings()
