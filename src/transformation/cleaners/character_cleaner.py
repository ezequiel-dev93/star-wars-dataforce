from __future__ import annotations
import re
from typing import Any
import pandas as pd
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)
_UNKNOWN = {'unknown', 'n/a', 'none', '', 'na'}


def _to_float(value: Any) -> float | None:
    try:
        cleaned = str(value).replace(',', '.').strip()
        return None if cleaned.lower() in _UNKNOWN else float(cleaned)
    except (ValueError, TypeError):
        return None


def _to_slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    return re.sub(r'-{2,}', '-', s).strip('-')


def _extract_id(url: str) -> int | None:
    match = re.search(r'/(\d+)/?$', url)
    return int(match.group(1)) if match else None


class CharacterCleaner:
    """
    Transforma datos crudos de SWAPI en un DataFrame normalizado.
    Acepta mapas opcionales para resolver URLs a nombres legibles:
      - film_map:   {film_url: titulo}
      - planet_map: {planet_url: nombre_planeta}
    """

    def clean(
        self,
        raw: list[dict[str, Any]],
        film_map: dict[str, str] | None = None,
        planet_map: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Limpia y normaliza personajes crudos de SWAPI.

        Args:
            raw:        Lista de dicts tal como los devuelve SWAPI.
            film_map:   Mapa {url -> titulo} para resolver appearances.
                        Si es None, se conservan las URLs originales.
            planet_map: Mapa {url -> nombre} para resolver homeworld.
                        Si es None, se conserva la URL original.

        Returns:
            DataFrame con columnas normalizadas.
        """
        if not raw:
            return pd.DataFrame()

        df = pd.DataFrame(raw)

        # Identificador numerico
        df['id'] = df['url'].apply(_extract_id)
        df = df.dropna(subset=['id'])
        df['id'] = df['id'].astype(int)

        # Slug URL-friendly
        df['slug'] = df['name'].apply(_to_slug)

        # Atributos fisicos
        df['height_cm'] = df['height'].apply(_to_float)
        df['mass_kg'] = df['mass'].apply(_to_float)
        for col in ('hair_color', 'eye_color', 'gender'):
            df[col] = df[col].apply(lambda v: None if str(v).lower() in _UNKNOWN else str(v))

        # Appearances: resolver URLs a titulos de peliculas
        if film_map:
            def resolve_films(film_urls: list) -> list[str]:
                if not isinstance(film_urls, list):
                    return []
                titles = [film_map.get(url, url) for url in film_urls]
                return titles
            df['appearances'] = df['films'].apply(resolve_films)
            logger.debug('appearances resueltos a titulos de peliculas.')
        else:
            df['appearances'] = df['films'].apply(lambda v: v if isinstance(v, list) else [])
            logger.warning('film_map no provisto: appearances contiene URLs en vez de titulos.')

        # Homeworld: resolver URL a nombre de planeta
        if planet_map:
            df['homeworld'] = df['homeworld'].apply(lambda v: planet_map.get(v, v) if v else None)
            logger.debug('homeworld resueltos a nombres de planetas.')

        logger.info(f'[bold green]Limpieza:[/] {len(df)} personajes procesados.')
        return df[[
            'id', 'slug', 'name',
            'height_cm', 'mass_kg', 'hair_color', 'eye_color',
            'gender', 'homeworld', 'appearances',
        ]].copy()
