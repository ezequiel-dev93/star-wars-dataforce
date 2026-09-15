"""
Caso de uso: Extracción de personajes de series y películas con Scrapling.

Flujo:
1. Filtra y rechaza producciones animadas para evitar ilustraciones/dibujos.
2. Extrae fichas oficiales desde StarWars.com Databank (Scrapling) con fallback a Wookieepedia.
3. Descarga imágenes en alta resolución localmente (evitando re-descargas de lo que ya existe).
4. Aplica deduplicación inteligente y fusión (merge) para evitar personajes repetidos y consolidar apariciones.
5. Persiste el dataset consolidado en characters.json.
"""
from __future__ import annotations
import asyncio
import re
from pathlib import Path

from src.core.entities.character import CharacterEntity, PhysicalTraits, BirthInfo, DeathInfo, normalize_slug
from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper, DatabankCharacterData
from src.infrastructure.scraping.wookieepedia_scraper import WookieepediaScraper
from src.infrastructure.storage.image_downloader import ImageDownloader
from src.infrastructure.persistence.json_storage import JsonStorage
from src.application.services.deduplication_service import deduplicate_and_merge_characters
from src.config.logging.logger import get_logger
from src.config.series_characters import (
    is_animated,
    is_live_action,
    get_production_characters,
    list_live_action_productions,
    list_available_animated_series,
    is_clone_character,
)

logger = get_logger(__name__)


def _parse_height_cm(height_str: str | None) -> float | None:
    """Extrae altura en centímetros desde formatos como '1.8m', '180 cm', etc."""
    if not height_str:
        return None
    match_m = re.search(r'(\d+[\.,]?\d*)\s*m', height_str, re.IGNORECASE)
    if match_m:
        try:
            return float(match_m.group(1).replace(',', '.')) * 100
        except ValueError:
            pass
    match_cm = re.search(r'(\d+)\s*cm', height_str, re.IGNORECASE)
    if match_cm:
        try:
            return float(match_cm.group(1))
        except ValueError:
            pass
    return None


class ExtractDatabankSeriesUseCase:
    """
    Coordina la extracción robusta de producciones de Star Wars:
    Scraping con Scrapling + Descarga de imágenes + Deduplicación y merge.
    """

    def __init__(
        self,
        databank_scraper: StarWarsDatabankScraper | None = None,
        storage: JsonStorage | None = None,
        image_downloader: ImageDownloader | None = None,
    ) -> None:
        self._databank = databank_scraper or StarWarsDatabankScraper()
        self._storage = storage or JsonStorage()
        self._image_downloader = image_downloader or ImageDownloader()

    async def execute(self, series_slug: str) -> Path:
        """Extrae personajes de una sola producción."""
        return await self.execute_multiple([series_slug])

    async def execute_multiple(self, series_slugs: list[str]) -> Path:
        """
        Extrae personajes de una o más producciones de Star Wars.
        """
        # 1. Validar y clasificar producciones
        valid_productions = []
        animated_available = list_available_animated_series()
        for slug in series_slugs:
            clean_slug = slug.strip().lower().replace("_", "-")
            if is_live_action(clean_slug):
                valid_productions.append(clean_slug)
            elif clean_slug in animated_available:
                valid_productions.append(clean_slug)
            elif is_animated(clean_slug):
                logger.warning(
                    f"[SKIP ANIMADA] '{clean_slug}' es una serie animada sin lista curada todavía. "
                    f"Disponibles curadas: {', '.join(animated_available)}"
                )
            else:
                logger.warning(
                    f"[SKIP DESCONOCIDA] '{clean_slug}' no está en el catálogo de producciones registradas."
                )

        if not valid_productions:
            logger.warning("No hay producciones válidas para procesar.")
            return self._storage.output_path

        logger.info(f"[bold blue]== Procesando {len(valid_productions)} producción(es) ==[/]")

        # 2. Obtener lista de personajes únicos a procesar
        character_names: list[str] = []
        for slug in valid_productions:
            names = get_production_characters(slug)
            character_names.extend(names)
            logger.info(f"  - {slug}: {len(names)} personajes")

        unique_names: list[str] = []
        seen = set()
        for name in character_names:
            norm = normalize_slug(name)
            if norm not in seen:
                seen.add(norm)
                unique_names.append(name)

        logger.info(f"[bold green]{len(unique_names)}[/] personajes únicos identificados.")

        # 3. Cargar personajes existentes
        existing_characters = self._storage.read()
        existing_map = {c.slug: c for c in existing_characters}
        next_id = max([c.id for c in existing_characters], default=0) + 1

        extracted_entities: list[CharacterEntity] = []

        # 4. Extracción con Scrapling
        async with self._databank:
            for name in unique_names:
                slug = normalize_slug(name)
                is_already_known = slug in existing_map
                logger.info(f"[PROCESANDO] {name} ({slug})... [Existente: {is_already_known}]")

                # Consultar Databank con Scrapling
                data: DatabankCharacterData | None = await self._databank.scrape_character_full(slug)

                description = data.description if data else ""
                image_url = data.image_url if data else ""
                appearances = data.appearances if data else []
                locations = data.locations if data else []
                species = data.species if data else []
                gender = data.gender.lower() if (data and data.gender) else None
                height_cm = _parse_height_cm(data.height) if data else None

                # Fallback de descripción a Wookieepedia si Databank no tenía suficiente
                if len(description.split()) < 15:
                    try:
                        async with WookieepediaScraper() as wiki:
                            wiki_desc = await wiki.scrape_description(name)
                            if len(wiki_desc.split()) > len(description.split()):
                                description = wiki_desc
                    except Exception as exc:
                        logger.debug(f"Wookieepedia fallback error para {name}: {exc}")

                # Identificar si es un soldado clon
                char_is_clone = is_clone_character(slug, name)
                affiliations: list[str] = []
                if char_is_clone:
                    affiliations.extend(["Clone Troopers", "Galactic Republic"])
                    if not species:
                        species = ["Human (Clone)"]
                    if not description:
                        description = f"{name} was a clone trooper who served in the Grand Army of the Republic."

                # Descargar imagen si tenemos URL
                avatar_path_str = ""
                # REGLA DE ORO: Si ya existe en live-action, NUNCA descargar dibujo animado.
                # Permitir imagen animada SOLAMENTE para personajes nuevos exclusivos de animación.
                allow_animated_img = not is_already_known

                if image_url:
                    saved_path = await self._image_downloader.download_character_image(
                        slug=slug,
                        image_url=image_url,
                        allow_animated=allow_animated_img,
                    )
                    if saved_path:
                        # Guardar ruta relativa para portabilidad
                        avatar_path_str = str(saved_path.as_posix())
                    elif is_already_known and existing_map[slug].avatar_url:
                        # Mantener foto de acción real previa
                        avatar_path_str = existing_map[slug].avatar_url
                    else:
                        avatar_path_str = image_url if allow_animated_img else ""
                elif is_already_known and existing_map[slug].avatar_url:
                    avatar_path_str = existing_map[slug].avatar_url

                # Crear entidad si obtuvimos al menos algo de información o si ya existía
                if description or image_url or is_already_known:
                    entity = CharacterEntity(
                        id=next_id,
                        slug=slug,
                        name=data.name if (data and data.name) else name,
                        physical_traits=PhysicalTraits(height_cm=height_cm),
                        gender=gender,
                        species=species,
                        planets=locations,
                        affiliations=affiliations,
                        masters=[],
                        apprentices=[],
                        description=description,
                        appearances=appearances,
                        portrayed_by=[],
                        birth=BirthInfo(),
                        death=DeathInfo(),
                        force_sensitive=False,
                        is_canon=True,
                        avatar_url=avatar_path_str,
                    )
                    extracted_entities.append(entity)
                    next_id += 1

                # Pausa humana respetuosa
                await asyncio.sleep(0.5)

        # 5. Fusión y Deduplicación Inteligente
        logger.info("[DEDUPLICACIÓN] Unificando y fusionando apariciones y datos...")
        all_consolidated = deduplicate_and_merge_characters(existing_characters + extracted_entities)

        # 6. Guardar en JSON
        output_path = self._storage.write(all_consolidated)
        logger.info(
            f"[bold green]Proceso completado:[/]\n"
            f"  - Total personajes consolidados: [bold]{len(all_consolidated)}[/]\n"
            f"  - Archivo guardado en: [cyan]{output_path}[/]"
        )

        return output_path
