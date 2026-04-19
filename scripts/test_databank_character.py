"""
Script para probar el scraper del Databank con un personaje individual.

Uso:
    uv run python scripts/test_databank_character.py "Din Djarin"
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper


async def main() -> None:
    character_name = sys.argv[1] if len(sys.argv) > 1 else "Din Djarin"

    scraper = StarWarsDatabankScraper()
    async with scraper:
        data = await scraper.scrape_character_full(character_name)

    if data:
        print(f"\n{'='*60}")
        print(f"Name: {data.name}")
        print(f"Description: {data.description[:200]}..." if len(data.description) > 200 else f"Description: {data.description}")
        print(f"Gender: {data.gender}")
        print(f"Height: {data.height}")
        print(f"Species: {data.species}")
        print(f"Locations: {data.locations}")
        print(f"Appearances: {data.appearances}")
        print(f"URL: {data.url}")
        print(f"{'='*60}")
    else:
        print(f"No se encontró información para: {character_name}")


if __name__ == '__main__':
    asyncio.run(main())
