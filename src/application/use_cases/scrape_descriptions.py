from __future__ import annotations
import asyncio, re
import pandas as pd
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from src.core.ports.scraper_port import ScraperPort
from src.shared.config.settings import settings
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)

def _to_slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    return re.sub(r'-{2,}', '-', s).strip('-')

class ScrapeDescriptionsUseCase:
    def __init__(self, scraper: ScraperPort) -> None:
        self._scraper = scraper

    async def execute(self, names: list[str]) -> pd.DataFrame:
        semaphore = asyncio.Semaphore(settings.scraping_concurrency)
        results: list[dict] = []

        async def scrape_one(name: str) -> dict:
            async with semaphore:
                desc = await self._scraper.scrape_description(name)
                return {'name': name, 'slug': _to_slug(name), 'description': desc}

        with Progress(SpinnerColumn(), TextColumn('{task.description}'),
                      BarColumn(), TaskProgressColumn()) as progress:
            task = progress.add_task('Scraping Wookieepedia...', total=len(names))
            for coro in asyncio.as_completed([scrape_one(n) for n in names]):
                results.append(await coro)
                progress.advance(task)

        logger.info('[bold green]Scraping completo.[/]')
        return pd.DataFrame(results)
