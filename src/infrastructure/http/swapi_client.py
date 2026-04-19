from __future__ import annotations
import asyncio
from typing import Any
import httpx
from src.core.ports.character_repository import CharacterRepositoryPort
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


class SwapiClient(CharacterRepositoryPort):

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.swapi_base_url,
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        )

    # Paginacion generica con retry

    async def _fetch_paginated(self, endpoint: str) -> list[dict[str, Any]]:
        """
        Descarga todos los resultados de un endpoint paginado de SWAPI.
        Maneja reintentos automaticos con backoff exponencial.
        """
        results: list[dict[str, Any]] = []
        url = endpoint
        page = 1
        while url:
            for attempt in range(1, settings.http_max_retries + 1):
                try:
                    resp = await self._client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    results.extend(data.get('results', []))
                    next_url = data.get('next')
                    url = next_url.replace(settings.swapi_base_url, '') if next_url else None
                    page += 1
                    break
                except httpx.HTTPError as exc:
                    logger.warning(f'[{endpoint}] intento {attempt}/{settings.http_max_retries}: {exc}')
                    if attempt == settings.http_max_retries:
                        raise
                    await asyncio.sleep(2 ** attempt)
        return results

    def _build_url_name_map(self, items: list[dict[str, Any]], name_key: str = 'name') -> dict[str, str]:
        # Construye un mapa {url: nombre} a partir de resultados de SWAPI.
        return {item['url']: item[name_key] for item in items if 'url' in item and name_key in item}

    # Personajes

    async def fetch_all(self) -> list[dict[str, Any]]:
        # Descarga todos los personajes paginando automaticamente.
        characters = await self._fetch_paginated('/people/')
        logger.info(f'[bold green]SWAPI:[/] {len(characters)} personajes descargados.')
        return characters

    async def fetch_by_id(self, character_id: int) -> dict[str, Any] | None:
        try:
            resp = await self._client.get(f'/people/{character_id}/')
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    # Peliculas — mapa {url -> titulo}

    async def fetch_films(self) -> dict[str, str]:
        """Retorna {film_url: titulo} ordenado por episode_id."""
        films = await self._fetch_paginated('/films/')
        films_sorted = sorted(films, key=lambda f: f.get('episode_id', 0))
        film_map = {f['url']: f['title'] for f in films_sorted}
        logger.info(f'[bold green]Films:[/] {len(film_map)} peliculas cargadas.')
        return film_map

    # Planetas — mapa {url -> nombre}

    async def fetch_planets(self) -> dict[str, str]:
        """Retorna {planet_url: nombre}."""
        planets = await self._fetch_paginated('/planets/')
        planet_map = self._build_url_name_map(planets)
        logger.info(f'[bold green]Planets:[/] {len(planet_map)} planetas cargados.')
        return planet_map

    # Especies — mapa {url -> nombre}

    async def fetch_species(self) -> dict[str, str]:
        """Retorna {species_url: nombre} (ej: '.../species/1/' -> 'Human')."""
        species = await self._fetch_paginated('/species/')
        species_map = self._build_url_name_map(species)
        logger.info(f'[bold green]Species:[/] {len(species_map)} especies cargadas.')
        return species_map

    # Context manager

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> 'SwapiClient':
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
