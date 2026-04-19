from __future__ import annotations
from pathlib import Path
from pydantic import ValidationError

from src.core.entities.character import CharacterEntity
from src.core.ports.character_repository import CharacterRepositoryPort
from src.application.mappers.swapi_mapper import SwapiMapper
from src.infrastructure.persistence.json_storage import JsonStorage
from src.application.use_cases.extract_characters import ExtractCharactersUseCase
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


class ExtractSwapiPipelineUseCase:
    """
    Orquesta el pipeline ETL de SWAPI:
      1. Carga catalogos de peliculas, planetas y especies
      2. Extrae personajes de SWAPI
      3. Traduce keys y resuelve URLs mediante el mapper
      4. Valida con Pydantic (toda la limpieza ocurre aqui)
      5. Persiste a JSON
    """

    def __init__(
        self,
        repository: CharacterRepositoryPort,
        mapper: SwapiMapper | None = None,
        storage: JsonStorage | None = None,
    ) -> None:
        self._repository = repository
        self._mapper = mapper or SwapiMapper()
        self._storage = storage or JsonStorage()

    async def execute(self) -> Path:
        logger.info('[bold blue]== Extrayendo Personajes base desde SWAPI ==[/]')

        # 1. Cargar catalogos de referencia
        film_map: dict[str, str] = {}
        planet_map: dict[str, str] = {}
        species_map: dict[str, str] = {}
        if hasattr(self._repository, 'fetch_films'):
            film_map = await self._repository.fetch_films()
        if hasattr(self._repository, 'fetch_planets'):
            planet_map = await self._repository.fetch_planets()
        if hasattr(self._repository, 'fetch_species'):
            species_map = await self._repository.fetch_species()

        # 2. Extraer personajes crudos
        raw_characters = await ExtractCharactersUseCase(self._repository).execute()

        # 3. Traducir keys y resolver URLs (sin limpiar datos, eso lo hace Pydantic)
        mapped_data = self._mapper.map_to_dicts(
            raw_characters,
            film_map=film_map,
            planet_map=planet_map,
            species_map=species_map,
        )

        # 4. Validar con Pydantic (coercion, slugs, "unknown" -> None, todo ocurre aqui)
        characters: list[CharacterEntity] = []
        errors = 0

        for row in mapped_data:
            try:
                entity = CharacterEntity.model_validate(row)
                characters.append(entity)
            except ValidationError as exc:
                errors += 1
                logger.warning(f'Validacion fallida [{row.get("name", "?")}]: {exc}')

        logger.info(
            f'Validacion finalizada: [bold green]{len(characters)}[/] OK | [bold red]{errors}[/] errores.'
        )

        # 5. Persistir
        output = self._storage.write(characters)
        logger.info('[bold blue]== Pipeline SWAPI Finalizado ==[/]')
        return output
