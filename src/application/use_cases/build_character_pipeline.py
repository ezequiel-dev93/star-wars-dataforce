from __future__ import annotations
from pathlib import Path
from pydantic import ValidationError
from src.core.entities.character import CharacterEntity, PhysicalTraits
from src.core.ports.character_repository import CharacterRepositoryPort
from src.core.ports.scraper_port import ScraperPort
from src.transformation.cleaners.character_cleaner import CharacterCleaner
from src.transformation.mergers.character_merger import CharacterMerger
from src.infrastructure.persistence.json_writer import JsonWriter
from src.application.use_cases.extract_characters import ExtractCharactersUseCase
from src.application.use_cases.scrape_descriptions import ScrapeDescriptionsUseCase
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class BuildCharacterPipelineUseCase:
    """
    Orquesta el pipeline ETL completo:
      1. Carga catalogos de películas y planetas (una sola vez)
      2. Extrae personajes de SWAPI
      3. Limpia y normaliza con Pandas (resolviendo URLs a nombres)
      4. Scrapea descripciones de Wookieepedia
      5. Mergea las fuentes
      6. Valida con Pydantic
      7. Persiste a JSON
    """

    def __init__(
        self,
        repository: CharacterRepositoryPort,
        scraper: ScraperPort,
        cleaner: CharacterCleaner | None = None,
        merger: CharacterMerger | None = None,
        writer: JsonWriter | None = None,
    ) -> None:
        self._repository = repository
        self._scraper = scraper
        self._cleaner = cleaner or CharacterCleaner()
        self._merger = merger or CharacterMerger()
        self._writer = writer or JsonWriter()

    async def execute(self) -> Path:
        logger.info('[bold blue]== Star Wars Dataforce Pipeline ==[/]')

        # 1. Cargar catálogos de referencia (solo 2 requests adicionales)
        film_map: dict[str, str] = {}
        planet_map: dict[str, str] = {}
        if hasattr(self._repository, 'fetch_films'):
            film_map = await self._repository.fetch_films()
        if hasattr(self._repository, 'fetch_planets'):
            planet_map = await self._repository.fetch_planets()

        # 2. Extraer personajes
        raw = await ExtractCharactersUseCase(self._repository).execute()

        # 3. Limpiar con mapas de resolucion
        clean_df = self._cleaner.clean(raw, film_map=film_map, planet_map=planet_map)

        # 4. Scrapear descripciones
        descriptions_df = await ScrapeDescriptionsUseCase(self._scraper).execute(
            clean_df['name'].tolist()
        )

        # 5. Merge
        merged_df = self._merger.merge(clean_df, descriptions_df)

        # 6. Validar con Pydantic
        characters: list[CharacterEntity] = []
        errors = 0
        for _, row in merged_df.iterrows():
            try:
                entity = CharacterEntity(
                    id=int(row['id']),
                    slug=row['slug'],
                    name=row['name'],
                    physical_traits=PhysicalTraits(
                        height_cm=row.get('height_cm'),
                        mass_kg=row.get('mass_kg'),
                        hair_color=row.get('hair_color'),
                        eye_color=row.get('eye_color'),
                    ),
                    gender=row.get('gender'),
                    homeworld=row.get('homeworld'),
                    appearances=row.get('appearances', []),
                    description=row.get('description', ''),
                )
                characters.append(entity)
            except ValidationError as exc:
                errors += 1
                logger.warning(f'Validacion fallida [{row.get("name", "?")}]: {exc}')

        logger.info(
            f'Validacion: [bold green]{len(characters)}[/] OK | [bold red]{errors}[/] errores.'
        )

        # 7. Persistir
        output = self._writer.write(characters)
        logger.info('[bold blue]== Pipeline finalizado ==[/]')
        return output
