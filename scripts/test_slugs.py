"""Test para encontrar slugs correctos en el Databank."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper


async def test_slug(scraper: StarWarsDatabankScraper, slug: str) -> None:
    """Prueba un slug y muestra resultado."""
    data = await scraper.scrape_character_full(slug)
    if data and data.description:
        print(f"[OK] {slug}: {data.name}")
        print(f"     Desc: {data.description[:80]}...")
        print(f"     Apps: {data.appearances}")
    else:
        print(f"[FAIL] {slug}: No encontrado o sin descripcion")


async def main() -> None:
    slugs_to_test = [
        # The Mandalorian
        'the-mandalorian',
        'din-djarin',
        'mandalorian',
        'din-djarin-the-mandalorian',
        # Migs Mayfeld
        'migs-mayfeld',
        'mayfeld',
        # Kuiil
        'kuiil',
        'kuill',
        # IG-11
        'ig-11',
        'ig11',
        'ig-eleven',
    ]

    scraper = StarWarsDatabankScraper()
    async with scraper:
        for slug in slugs_to_test:
            await test_slug(scraper, slug)
            print()
            await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
