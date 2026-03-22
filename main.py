from __future__ import annotations
import asyncio
from src.infrastructure.http.swapi_client import SwapiClient
from src.infrastructure.scraping.wookieepedia_scraper import WookiepediaScraper
from src.application.use_cases.build_character_pipeline import BuildCharacterPipelineUseCase
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)

async def main() -> None:
    async with SwapiClient() as repository:
        async with WookiepediaScraper() as scraper:
            pipeline = BuildCharacterPipelineUseCase(repository=repository, scraper=scraper)
            output = await pipeline.execute()
            logger.info(f'[bold]Resultado en:[/] [cyan]{output}[/]')

if __name__ == '__main__':
    asyncio.run(main())
