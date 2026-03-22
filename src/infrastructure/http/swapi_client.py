from __future__ import annotations
import asyncio
from typing import Any
import httpx
from src.core.ports.character_repository import CharacterRepositoryPort
from src.shared.config.settings import settings
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class SwapiClient(CharacterRepositoryPort):
    """Cliente HTTP asincrono para la API publica SWAPI."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.swapi_base_url,
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Personajes
    # ──────────────────────────────────────────────────────────────────────

    async def fetch_all(self) -> list[dict[str, Any]]:
        """Descarga todos los personajes paginando automaticamente."""
        characters: list[dict[str, Any]] = []
        url = '/people/'
        page = 1
        while url:
            logger.debug(f'Fetching SWAPI page {page}')
            for attempt in range(1, settings.http_max_retries + 1):
                try:
                    resp = await self._client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    characters.extend(data.get('results', []))
                    next_url = data.get('next')
                    url = next_url.replace(settings.swapi_base_url, '') if next_url else None
                    page += 1
                    break
                except httpx.HTTPError as exc:
                    logger.warning(f'Intento {attempt}/{settings.http_max_retries}: {exc}')
                    if attempt == settings.http_max_retries:
                        raise
                    await asyncio.sleep(2 ** attempt)
        logger.info(f'[bold green]SWAPI:[/] {len(characters)} personajes descargados.')
        return characters

    async def fetch_by_id(self, character_id: int) -> dict[str, Any] | None:
        try:
            resp = await self._client.get(f'/people/{character_id}/')
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            return None if exc.response.status_code == 404 else (_ for _ in ()).throw(exc)

    # ──────────────────────────────────────────────────────────────────────
    # Peliculas — mapa {url -> titulo ordenado por episode_id}
    # ──────────────────────────────────────────────────────────────────────

    async def fetch_films(self) -> dict[str, str]:
        """
        Retorna un dict {film_url: titulo} con todas las peliculas de SWAPI.
        Ejemplo: {"https://swapi.dev/api/films/1/": "A New Hope"}
        """
        resp = await self._client.get('/films/')
        resp.raise_for_status()
        films = resp.json().get('results', [])
        # Ordenamos por episode_id para consistencia
        films_sorted = sorted(films, key=lambda f: f.get('episode_id', 0))
        film_map = {f['url']: f['title'] for f in films_sorted}
        logger.info(f'[bold green]Films:[/] {len(film_map)} peliculas cargadas: {list(film_map.values())}')
        return film_map

    # ──────────────────────────────────────────────────────────────────────
    # Planetas — mapa {url -> nombre}
    # ──────────────────────────────────────────────────────────────────────

    async def fetch_planets(self) -> dict[str, str]:
        """
        Retorna un dict {planet_url: nombre} con todos los planetas de SWAPI.
        Útil para resolver homeworld de URL a nombre legible.
        """
        planets: dict[str, str] = {}
        url = '/planets/'
        while url:
            resp = await self._client.get(url)
            resp.raise_for_status()
            data = resp.json()
            for p in data.get('results', []):
                planets[p['url']] = p['name']
            next_url = data.get('next')
            url = next_url.replace(settings.swapi_base_url, '') if next_url else None
        logger.info(f'[bold green]Planets:[/] {len(planets)} planetas cargados.')
        return planets

    # ──────────────────────────────────────────────────────────────────────
    # Context manager
    # ──────────────────────────────────────────────────────────────────────

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> 'SwapiClient':
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
