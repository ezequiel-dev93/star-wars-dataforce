from __future__ import annotations
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8', 'case_sensitive': False}
    swapi_base_url: str = Field(default='https://swapi.dev/api')
    wookieepedia_base_url: str = Field(default='https://starwars.fandom.com/wiki')
    http_timeout_seconds: float = Field(default=30.0)
    http_max_retries: int = Field(default=3)
    scraping_concurrency: int = Field(default=5)
    scraping_headless: bool = Field(default=True)
    output_path: Path = Field(default=Path('output/characters.json'))
    log_level: str = Field(default='INFO')
settings = Settings()
