"""
Script para extraer personajes de The Mandalorian desde el Databank.

Uso:
    uv run python scripts/extract_mandalorian_characters.py
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper, DatabankCharacterData
from src.infrastructure.persistence.json_storage import JsonStorage
from src.config.logging.logger import get_logger

logger = get_logger(__name__)

# Lista de slugs de personajes principales de The Mandalorian en el Databank
# Basada en el análisis de la página de la serie
MANDALORIAN_CHARACTERS = [
    'the-mandalorian',  # Din Djarin
    'grogu',
    'greef-karga',
    'the-client',
    'moff-gideon',
    'the-armorer',
    'paz-vizsla',
    'boba-fett',
    'bo-katan-kryze',
    'ahsoka-tano',
    'luke-skywalker',
    'peli-motto',
    'cara-dune',
    'migs-mayfeld',
    'fennec-shand',
    'jango-fett',
    'kuiil',
    'ig-11',
]


async def main() -> None:
    """Extrae personajes de The Mandalorian."""
    storage = JsonStorage()
    existing = storage.read()
    existing_slugs = {c.slug for c in existing}
    next_id = max([c.id for c in existing], default=0) + 1

    logger.info(f"Cargados {len(existing)} personajes existentes")
    logger.info(f"Scrapeando {len(MANDALORIAN_CHARACTERS)} personajes del Databank...")

    scraper = StarWarsDatabankScraper()
    new_characters = []
    skipped = 0
    failed = []

    async with scraper:
        for slug in MANDALORIAN_CHARACTERS:
            # Verificar si ya existe
            char_slug = slug.lower().replace('_', '-')
            if char_slug in existing_slugs:
                logger.info(f"[SKIP] {slug}: Ya existe en el archivo")
                skipped += 1
                continue

            # Scrapear del Databank
            data = await scraper.scrape_character_full(slug)
            if data and data.description:  # Solo si tiene descripcion valida
                from src.core.entities.character import CharacterEntity, PhysicalTraits

                entity = CharacterEntity(
                    id=next_id,
                    slug=char_slug,
                    name=data.name,
                    physical_traits=PhysicalTraits(),
                    gender=data.gender.lower() if data.gender else None,
                    species=data.species if data.species else [],
                    locations=data.locations if data.locations else None,
                    affiliations=[],
                    masters=[],
                    apprentices=[],
                    description=data.description,
                    appearances=data.appearances if data.appearances else [],
                    portrayed_by=[],
                    birth={},
                    death={},
                    force_sensitive=False,
                    is_canon=True,
                    avatar_url='',
                )
                new_characters.append(entity)
                existing_slugs.add(char_slug)
                next_id += 1
                logger.info(f"[OK] {data.name}: Agregado ({len(data.description)} chars)")
            else:
                failed.append(slug)
                logger.warning(f"[FAIL] {slug}: No se pudo extraer")

            await asyncio.sleep(1.5)  # Pausa entre requests

    # Guardar resultados
    if new_characters:
        all_characters = existing + new_characters
        output_path = storage.write(all_characters)
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Extracción completada")
        logger.info(f"   Nuevos personajes: {len(new_characters)}")
        logger.info(f"   Omitidos (duplicados): {skipped}")
        logger.info(f"   Fallidos: {len(failed)}")
        logger.info(f"   Total: {len(all_characters)}")
        logger.info(f"   Archivo: {output_path}")
        logger.info(f"{'='*60}")
    else:
        logger.info("\n⚠️  No se encontraron personajes nuevos")

    if failed:
        logger.info(f"\nPersonajes que no se pudieron extraer: {failed}")


if __name__ == '__main__':
    asyncio.run(main())
