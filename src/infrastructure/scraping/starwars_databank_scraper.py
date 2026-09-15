"""
Scraper de StarWars.com Databank implementado con Scrapling.

Utiliza Scrapling (Fetcher / StealthyFetcher) con fingerprinting TLS y evasión
nativa de WAFs (Akamai / Cloudflare), logrando ejecución headless rápida e invisible
sin necesidad de levantar ventanas gráficas de navegador.
"""
from __future__ import annotations
import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional

from scrapling import Fetcher, StealthyFetcher
from src.core.ports.scraper_port import ScraperPort
from src.config.settings import settings
from src.config.logging.logger import get_logger
from src.infrastructure.storage.image_downloader import clean_image_url, is_animated_image

logger = get_logger(__name__)


@dataclass
class DatabankCharacterData:
    """Datos estructurados extraídos de una ficha de Star Wars Databank."""
    name: str
    description: str = ""
    gender: Optional[str] = None
    height: Optional[str] = None
    species: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    appearances: list[str] = field(default_factory=list)
    image_url: str = ""
    url: str = ""


def _build_databank_slug(name: str) -> str:
    """Construye un slug compatible con URLs de Star Wars Databank."""
    normalized = name.strip().lower()
    accents = {
        'é': 'e', 'á': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n', 'î': 'i', 'ï': 'i'
    }
    for char, rep in accents.items():
        normalized = normalized.replace(char, rep)
    slug = re.sub(r'[^\w\s-]', '', normalized)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-{2,}', '-', slug)
    return slug.strip('-')


def _clean_text(text: str | None) -> str:
    """Limpia espacios y caracteres residuales."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\[\w+\]', '', text)
    return text.strip()


class StarWarsDatabankScraper(ScraperPort):
    """
    Scraper oficial de StarWars.com Databank utilizando Scrapling.
    """

    def __init__(self, timeout: int = 15) -> None:
        self._timeout = timeout

    async def __aenter__(self) -> StarWarsDatabankScraper:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        """Cierra recursos si los hubiera (Scrapling Fetcher es stateless)."""
        pass

    def _fetch_page_sync(self, url: str):
        """Petición síncrona con Fetcher y fallback a StealthyFetcher si hay bloqueo."""
        try:
            response = Fetcher.get(url, timeout=self._timeout)
            if response.status in (403, 503):
                logger.warning(f"[Databank] WAF detectado (status {response.status}). Activando StealthyFetcher...")
                stealth = StealthyFetcher()
                return stealth.fetch(url)
            return response
        except Exception as exc:
            logger.debug(f"[Databank] Error con Fetcher: {exc}. Intentando con StealthyFetcher...")
            stealth = StealthyFetcher()
            return stealth.fetch(url)

    async def _fetch_page(self, url: str):
        """Ejecuta la petición en un hilo para no bloquear el bucle de eventos asyncio."""
        return await asyncio.to_thread(self._fetch_page_sync, url)

    async def scrape_description(self, character_name: str) -> str:
        """Implementación del puerto ScraperPort para obtener descripción."""
        data = await self.scrape_character_full(character_name)
        return data.description if data else ""

    async def scrape_character_full(self, name_or_slug: str) -> DatabankCharacterData | None:
        """
        Extrae datos completos de la ficha del personaje en Star Wars Databank.
        """
        slug = _build_databank_slug(name_or_slug)
        url = f"{settings.starwars_databank_base_url.rstrip('/')}/{slug}"

        logger.debug(f"[Databank] Consultando: {url}")
        try:
            response = await self._fetch_page(url)
        except Exception as exc:
            logger.warning(f"[Databank] Error de conexión para '{name_or_slug}': {exc}")
            return None

        if not response or response.status != 200:
            logger.debug(f"[Databank] Ficha no encontrada (Status {getattr(response, 'status', 'None')}) para: {url}")
            return None

        # 1. Nombre
        page_title = response.css("title::text").get() or ""
        name = name_or_slug
        if page_title:
            clean_title = page_title.split("- Databank")[0].split("|")[0].strip()
            # Remover paréntesis como (Din Djarin) si queremos el nombre principal o mantenerlo
            if clean_title:
                name = clean_title

        # 2. Descripción (Meta description y párrafos del cuerpo)
        meta_desc = response.css('meta[name="description"]::attr(content)').get() or ""
        body_paras = response.css(
            ".rich-text-container p::text, "
            ".content-container p::text, "
            ".databank-content p::text, "
            ".module.rich_text p::text"
        ).getall()

        description_parts = []
        if meta_desc and "Experience Star Wars" not in meta_desc:
            description_parts.append(_clean_text(meta_desc))

        for p in body_paras:
            cleaned_p = _clean_text(p)
            if cleaned_p and len(cleaned_p) > 25 and cleaned_p not in description_parts:
                description_parts.append(cleaned_p)

        full_description = " ".join(description_parts).strip()
        if not full_description and meta_desc:
            full_description = _clean_text(meta_desc)

        # 3. Categorías y estadísticas (.stats-container .category)
        stats_map: dict[str, list[str]] = {}
        for cat in response.css(".stats-container .category"):
            heading = _clean_text(cat.css(".heading::text").get()).lower()
            values = [_clean_text(v) for v in cat.css(".property-name::text").getall()]
            values = [v for v in values if v]
            if heading and values:
                stats_map[heading] = values

        # Parsear stats
        species_list = stats_map.get("species", [])
        locations_list = stats_map.get("locations", [])
        appearances_list = stats_map.get("appearances", [])

        # Género y dimensiones si están presentes
        gender = None
        if "gender" in stats_map and stats_map["gender"]:
            gender = stats_map["gender"][0]

        height = None
        if "dimensions" in stats_map and stats_map["dimensions"]:
            height = stats_map["dimensions"][0]

        # 4. Imagen del personaje (Retrato principal)
        # Se busca en .aspect-container img o imagen principal descartando dibujos/animación
        image_url = ""
        portrait_imgs = response.css(".aspect-container img, .image-wrapper img, .thumb img")
        for img in portrait_imgs:
            src = img.attrib.get("data-src") or img.attrib.get("src")
            alt = img.attrib.get("alt") or ""
            if src and "lumiere" in src and "svg" not in src:
                if not is_animated_image(src, alt):
                    image_url = clean_image_url(src)
                    break

        # Fallback a cualquier imagen de lumiere con region (que no sea dibujo)
        if not image_url:
            for img in response.css("img"):
                src = img.attrib.get("data-src") or img.attrib.get("src")
                alt = img.attrib.get("alt") or ""
                if src and "lumiere" in src and "region=" in src and "svg" not in src:
                    if not is_animated_image(src, alt):
                        image_url = clean_image_url(src)
                        break

        return DatabankCharacterData(
            name=name,
            description=full_description,
            gender=gender,
            height=height,
            species=species_list,
            locations=locations_list,
            appearances=appearances_list,
            image_url=image_url,
            url=url,
        )
