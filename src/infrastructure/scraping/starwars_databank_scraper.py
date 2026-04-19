from __future__ import annotations
import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from src.core.ports.scraper_port import ScraperPort
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)

@dataclass
class DatabankCharacterData:
    # Datos completos de un personaje del Databank.
    name: str
    description: str = ''
    gender: Optional[str] = None
    height: Optional[str] = None
    species: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    appearances: list[str] = field(default_factory=list)
    url: str = ''


# Selectores específicos para StarWars.com Databank (basados en análisis de HTML real)
# La estructura usa módulos de Matterhorn CMS
_DESCRIPTION_SELECTORS = [
    # Meta description (más confiable para la descripción principal)
    'meta[name="description"]',
    # Contenido principal en módulos de texto
    '.module.rich_text p',
    '[data-module-type="rich_text"] p',
    '.content-body p',
]

# Para datos de la ficha técnica - StarWars Databank usa dt/dd o divs específicos
_DATA_SELECTORS = {
    'gender': [
        'dt:has-text("Gender") + dd',
        'div:has(dt:has-text("Gender")) dd',
        '[class*="gender"]',
    ],
    'height': [
        'dt:has-text("Height") + dd',
        'div:has(dt:has-text("Height")) dd',
        '[class*="height"]',
    ],
    'species': [
        'dt:has-text("Species") + dd',
        'div:has(dt:has-text("Species")) dd',
        '[class*="species"]',
    ],
}

# Selectores de cookies
_CONSENT_SELECTORS = [
    'button[id*="accept"]',
    '#onetrust-accept-btn-handler',
    'button[aria-label*="Accept"]',
]


def _build_databank_slug(name: str) -> str:
    # Construye slug compatible con URLs de Databank.
    normalized = name.strip().lower()
    # El Databank usa guiones simples y no tiene acentos en URLs
    for char, replacement in {'é': 'e', 'á': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n'}.items():
        normalized = normalized.replace(char, replacement)
    # Remover caracteres especiales excepto letras, números, espacios y guiones
    slug = re.sub(r'[^\w\s-]', '', normalized)
    # Reemplazar espacios múltiples con guión simple
    slug = re.sub(r'[\s_]+', '-', slug)
    # Eliminar guiones múltiples
    slug = re.sub(r'-{2,}', '-', slug)
    return slug.strip('-')


def _clean_description(text: str) -> str:
    # Limpia texto de descripción
    if not text:
        return ""
    # Detectar mensajes de error
    if any(x in text.lower() for x in ['404', 'sorry', 'not found', 'error']):
        if len(text) < 200:  # Mensajes cortos de error
            return ""
    # Limpiar espacios
    text = re.sub(r'\s+', ' ', text)
    # Remover "Read More" y similares
    text = re.sub(r'\s*(READ MORE|Read More|show more|SHOW MORE)\s*$', '', text, flags=re.IGNORECASE)
    return text.strip()


def _clean_text(text: str) -> str:
    # Limpia texto general.
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text).strip()
    # Remover etiquetas como [Show], [Hide], etc.
    text = re.sub(r'\[\w+\]', '', text)
    return text.strip()


def _extract_meta_content(html: str, property_name: str) -> str:
    #Extrae contenido de meta tags del HTML.
    # Pattern para meta description
    pattern = f'<meta[^>]+name="{property_name}"[^>]+content="([^"]*)"'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1)
    # Pattern alternativo
    pattern = f'<meta[^>]+content="([^"]*)"[^>]+name="{property_name}"'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1)
    return ''


class StarWarsDatabankScraper(ScraperPort):
    """
    Scraper de StarWars.com Databank.
    NOTA: Requiere headless=False para evitar bloqueo de Akamai.
    """

    def __init__(self, headless: bool = False) -> None:
        self._playwright = None
        self._browser: Browser | None = None
        self._headless = headless

    async def _ensure_browser(self) -> Browser:
        # Inicializa el browser de Playwright si no existe.
        if self._browser is None:
            self._playwright = await async_playwright().start()
            args = ['--disable-blink-features=AutomationControlled']
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,  # Databank generalmente requiere headless=False
                args=args,
            )
        return self._browser

    async def _dismiss_consent(self, page: Page) -> None:
        # Intenta cerrar banners de cookies/GDPR.
        for selector in _CONSENT_SELECTORS:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2_000):
                    await btn.click(timeout=2_500)
                    await page.wait_for_timeout(500)
                    return
            except Exception:
                continue

    async def _extract_from_meta(self, page: Page) -> str:
        # Extrae descripción del meta tag.
        try:
            meta = await page.query_selector('meta[name="description"]')
            if meta:
                content = await meta.get_attribute('content')
                if content:
                    return _clean_description(content)
        except Exception:
            pass
        return ''

    async def _extract_from_content(self, page: Page) -> str:
        #Extrae descripción del contenido principal.
        for selector in _DESCRIPTION_SELECTORS[1:]:  # Skip meta, ya probado
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    text = await el.inner_text()
                    cleaned = _clean_description(text)
                    # Solo aceptar descripciones de longitud razonable
                    if len(cleaned) > 50 and len(cleaned) < 500:
                        return cleaned
            except Exception:
                continue
        return ''

    async def _extract_stats_section(self, page: Page) -> dict[str, str]:
        # Extrae datos de la sección de estadísticas/ficha técnica.
        stats = {}
        try:
            # Buscar la sección de stats en el formato del Databank
            # Usa dt/dd pairs o divs con clases específicas
            stats_container = await page.query_selector('[class*="stats"], [class*="databank-stats"], .module.display')
            if stats_container:
                # Buscar todos los dt/dd dentro del contenedor
                dts = await stats_container.query_selector_all('dt')
                for dt in dts:
                    label = await dt.inner_text()
                    label = _clean_text(label).lower()
                    # El siguiente dd contiene el valor
                    dd = await dt.evaluate('el => el.nextElementSibling')
                    if dd:
                        value = await page.evaluate('el => el.innerText', dd)
                        value = _clean_text(value)
                        if value and value.lower() not in ('unknown', 'n/a', '', 'none', 'default'):
                            stats[label] = value
        except Exception as exc:
            logger.debug(f"Error extrayendo stats: {exc}")
        return stats

    async def _extract_appearances(self, page: Page) -> list[str]:
        # Extrae apariciones en series/películas.
        results = []
        seen = set()

        # Títulos de series/películas válidos del Databank
        valid_prefixes = (
            'Star Wars: The Mandalorian',
            'Star Wars: The Book of Boba Fett',
            'Star Wars: The Clone Wars',
            'Star Wars: Rebels',
            'Star Wars: Andor',
            'Star Wars: Obi-Wan Kenobi',
            'Star Wars: Ahsoka',
            'Star Wars: Skeleton Crew',
            'Star Wars: The Acolyte',
        )

        try:
            links = await page.query_selector_all('a')
            for link in links:
                text = await link.inner_text()
                cleaned = _clean_text(text)
                # Solo incluir series/películas específicas
                if cleaned and cleaned.startswith(valid_prefixes):
                    if cleaned.lower() not in seen and len(cleaned) < 50:
                        seen.add(cleaned.lower())
                        results.append(cleaned)
        except Exception:
            pass

        return results

    async def scrape_character_full(self, name_or_slug: str) -> DatabankCharacterData | None:
        # Scrapea datos completos de un personaje del Databank.
        browser = await self._ensure_browser()
        slug = _build_databank_slug(name_or_slug)
        url = f"{settings.starwars_databank_base_url}/{slug}"

        logger.debug(f"[Databank] Scrapeando: {url}")

        page = await browser.new_page()
        try:
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.5",
            })

            await page.goto(url, wait_until="networkidle", timeout=settings.scraping_page_timeout_ms)
            await asyncio.sleep(2)
            await self._dismiss_consent(page)

            # Extraer nombre del título
            name = name_or_slug
            try:
                title_el = await page.query_selector('title')
                if title_el:
                    title_text = await title_el.inner_text()
                    # El título es formato: "Nombre - Databank | StarWars.com"
                    if ' - Databank' in title_text:
                        name = title_text.split(' - Databank')[0].strip()
                        # Remover subtítulo entre paréntesis
                        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
            except Exception:
                pass

            # Extraer descripción - primero intentar meta
            description = await self._extract_from_meta(page)
            if not description:
                description = await self._extract_from_content(page)

            # Extraer datos técnicos de la sección de stats
            stats = await self._extract_stats_section(page)
            gender = stats.get('gender')
            height = stats.get('height')
            species = [stats['species']] if 'species' in stats else []

            # Extraer apariciones
            appearances = await self._extract_appearances(page)

            # Si no hay descripción ni datos, probablemente es 404
            if not description and not gender and not species and not height:
                logger.warning(f"[Databank] {name!r}: Parece ser 404 o sin datos")
                return None

            data = DatabankCharacterData(
                name=name,
                description=description,
                gender=gender,
                height=height,
                species=species if species else [],
                locations=[],  # El Databank no tiene ubicaciones claras
                appearances=appearances,
                url=url,
            )

            logger.info(f"[Databank] {name!r}: Extraído con éxito")
            return data

        except Exception as exc:
            logger.warning(f"[Databank] {name_or_slug!r}: Error: {exc}")
            return None
        finally:
            await page.close()

    async def scrape_series_characters(self, series_slug: str) -> list[DatabankCharacterData]:
        """
        Scrapea personajes de una serie del Databank.
        NOTA: Esta función es experimental - el Databank no tiene una API clara
        para extraer todos los personajes de una serie.
        """
        logger.warning(f"[Databank] scrape_series_characters es experimental para {series_slug}")
        # Por ahora, devolver lista vacía - necesitaría análisis más profundo.
        return []

    async def scrape_description(self, name: str) -> str:
        # Implementación del ScraperPort - solo devuelve descripción.
        data = await self.scrape_character_full(name)
        return data.description if data else ''

    async def close(self) -> None:
        # Cierra el browser y libera recursos.
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = self._playwright = None

    async def __aenter__(self) -> 'StarWarsDatabankScraper':
        await self._ensure_browser()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
