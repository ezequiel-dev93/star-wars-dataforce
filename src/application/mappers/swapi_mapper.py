from __future__ import annotations
import re
from typing import Any
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


def _extract_id(url: str) -> int | None:
    """Extrae el ID numerico de una URL de SWAPI."""
    match = re.search(r'/(\d+)/?$', url)
    return int(match.group(1)) if match else None


def _resolve_url_list(urls: Any, url_map: dict[str, str]) -> list[str]:
    """Resuelve una lista de URLs de SWAPI a nombres usando un mapa."""
    if not isinstance(urls, list):
        return []
    return [url_map.get(url, url) for url in urls]


class SwapiMapper:
    """
    Data Mapper de Aplicacion (SRP: solo traduce keys y resuelve URLs).
    
    NO limpia datos, NO parsea floats, NO genera slugs.
    Esa responsabilidad recae en Pydantic (CharacterEntity).
    
    Acepta mapas opcionales para resolver URLs a nombres legibles:
      - film_map:    {film_url: titulo}
      - planet_map:  {planet_url: nombre_planeta}
      - species_map: {species_url: nombre_especie}
    """

    def map_to_dicts(
        self,
        raw: list[dict[str, Any]],
        film_map: dict[str, str] | None = None,
        planet_map: dict[str, str] | None = None,
        species_map: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Traduce datos crudos de SWAPI al esquema de CharacterEntity."""
        if not raw:
            return []

        results: list[dict[str, Any]] = []

        for item in raw:
            # Extraer ID desde la URL
            char_id = _extract_id(item.get('url', ''))
            if char_id is None:
                continue

            name = item.get('name', '')

            # Resolver URLs a nombres legibles
            appearances = _resolve_url_list(
                item.get('films', []),
                film_map or {},
            )
            species = _resolve_url_list(
                item.get('species', []),
                species_map or {},
            )

            # Planeta: resolver URL unica a nombre
            homeworld = item.get('homeworld')
            planets = (
                planet_map.get(homeworld, homeworld)
                if planet_map and homeworld
                else homeworld
            )

            # Construir diccionario con keys del esquema CharacterEntity.
            # Pydantic se encarga de: slug, coercion de floats, limpiar "unknown", etc.
            results.append({
                'id': char_id,
                'slug': name,  # Pydantic lo normaliza via build_slug
                'name': name,
                'physical_traits': {
                    'height_cm': item.get('height'),
                    'mass_kg': item.get('mass'),
                    'hair_color': item.get('hair_color'),
                    'eye_color': item.get('eye_color'),
                },
                'gender': item.get('gender'),
                'planets': planets,
                'species': species,
                'appearances': appearances,
                'birth': {'year': item.get('birth_year')},
            })

        logger.info(f'[bold green]Mapeo finalizado:[/] {len(results)} personajes traducidos.')
        return results
