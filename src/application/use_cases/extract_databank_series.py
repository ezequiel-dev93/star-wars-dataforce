from __future__ import annotations
import asyncio
import re
from pathlib import Path
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn,
)

from src.core.entities.character import CharacterEntity, PhysicalTraits, BirthInfo, DeathInfo, normalize_slug
from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper, DatabankCharacterData
from src.infrastructure.persistence.json_storage import JsonStorage
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


class ExtractDatabankSeriesUseCase:
    """
    Extrae personajes de una serie del Databank y los agrega al JSON existente.
    Evita duplicados basándose en el slug del nombre.
    """

    def __init__(
        self,
        scraper: StarWarsDatabankScraper | None = None,
        storage: JsonStorage | None = None,
    ) -> None:
        self._scraper = scraper
        self._storage = storage or JsonStorage()

    def _databank_to_entity(self, data: DatabankCharacterData, next_id: int) -> CharacterEntity:
        """Convierte datos del Databank a CharacterEntity."""

        # Parsear height
        height_cm = None
        if data.height:
            # Buscar número en el texto (ej: "1.72 m" -> 172)
            match = re.search(r'(\d+[\.,]?\d*)\s*m', data.height, re.IGNORECASE)
            if match:
                try:
                    height_m = float(match.group(1).replace(',', '.'))
                    height_cm = height_m * 100
                except ValueError:
                    pass
            # También buscar en cm directamente
            match_cm = re.search(r'(\d+)\s*cm', data.height, re.IGNORECASE)
            if match_cm:
                try:
                    height_cm = float(match_cm.group(1))
                except ValueError:
                    pass

        return CharacterEntity(
            id=next_id,
            slug=normalize_slug(data.name),
            name=data.name,
            physical_traits=PhysicalTraits(
                height_cm=height_cm,
                mass_kg=None,
                hair_color=None,
                eye_color=None,
            ),
            gender=data.gender.lower() if data.gender else None,
            species=data.species if data.species else [],
            planets=', '.join(data.locations) if data.locations else None,
            affiliations=[],
            masters=[],
            apprentices=[],
            description=data.description,
            appearances=data.appearances if data.appearances else [],
            portrayed_by=[],
            birth=BirthInfo(),
            death=DeathInfo(),
            force_sensitive=False,
            is_canon=True,
            avatar_url='',
        )

    async def execute(self, series_slug: str) -> Path:
        """
        Ejecuta la extracción de personajes de una serie.

        Args:
            series_slug: Slug de la serie (ej: 'the-mandalorian', 'andor')

        Returns:
            Path al archivo actualizado
        """
        logger.info(f"[bold blue]== Extrayendo personajes de serie: {series_slug} ==[/]")

        # 1. Leer personajes existentes
        existing_characters = self._storage.read()
        existing_slugs = {c.slug for c in existing_characters}
        next_id = max([c.id for c in existing_characters], default=0) + 1

        logger.info(f"[bold green]{len(existing_characters)}[/] personajes ya existen en el archivo.")

        # 2. Scrapear serie
        scraper = self._scraper or StarWarsDatabankScraper()
        async with scraper:
            databank_chars = await scraper.scrape_series_characters(series_slug)

        if not databank_chars:
            logger.warning(f"No se encontraron personajes nuevos en {series_slug}")
            return self._storage.output_path

        # 3. Filtrar duplicados y convertir
        new_characters = []
        skipped = 0

        for db_char in databank_chars:
            char_slug = normalize_slug(db_char.name)
            if char_slug in existing_slugs:
                logger.debug(f"Personaje ya existe: {db_char.name}")
                skipped += 1
                continue

            entity = self._databank_to_entity(db_char, next_id)
            new_characters.append(entity)
            existing_slugs.add(char_slug)
            next_id += 1

        if not new_characters:
            logger.info(f"Todos los personajes de {series_slug} ya existen.")
            return self._storage.output_path

        # 4. Guardar
        all_characters = existing_characters + new_characters
        output_path = self._storage.write(all_characters)

        logger.info(
            f"[bold green]Extracción completada:[/] "
            f"[green]{len(new_characters)}[/] nuevos personajes agregados | "
            f"[yellow]{skipped}[/] omitidos (duplicados) | "
            f"Total: [bold]{len(all_characters)}[/]"
        )

        return output_path

    async def execute_multiple(self, series_slugs: list[str]) -> Path:
        """
        Extrae personajes de múltiples series.

        Args:
            series_slugs: Lista de slugs de series

        Returns:
            Path al archivo actualizado
        """
        logger.info(f"[bold blue]== Extrayendo de {len(series_slugs)} series ==[/]")

        all_new_chars = []
        existing_characters = self._storage.read()
        existing_slugs = {c.slug for c in existing_characters}
        next_id = max([c.id for c in existing_characters], default=0) + 1

        scraper = self._scraper or StarWarsDatabankScraper()

        async with scraper:
            for series_slug in series_slugs:
                databank_chars = await scraper.scrape_series_characters(series_slug)

                for db_char in databank_chars:
                    char_slug = normalize_slug(db_char.name)
                    if char_slug in existing_slugs:
                        continue

                    entity = self._databank_to_entity(db_char, next_id)
                    all_new_chars.append(entity)
                    existing_slugs.add(char_slug)
                    next_id += 1

                await asyncio.sleep(2)  # Pausa entre series

        if not all_new_chars:
            logger.info("No se encontraron personajes nuevos.")
            return self._storage.output_path

        all_characters = existing_characters + all_new_chars
        output_path = self._storage.write(all_characters)

        logger.info(f"[bold green]Total nuevos personajes agregados: {len(all_new_chars)}[/]")

        return output_path
