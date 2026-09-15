from __future__ import annotations
import asyncio
import re
from urllib.parse import quote
from playwright.async_api import Page
from src.infrastructure.scraping.base_playwright_scraper import BasePlaywrightScraper
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)

# Selectores CSS en cascada (orden de prioridad) | Fandom/Wookieepedia
_CONTENT_SELECTORS = [
    '#content p',
    '.mw-parser-output > p',
    '#mw-content-text .mw-parser-output p',
    '.page-content p',
    'article p',
]

# Consent específicos de Fandom
_WOOKIEEEPEDIA_CONSENT_SELECTORS = [
    '[data-tracking-opt-in-accept]',
    '.NN0_TB_DIs498iAction--accept',
    'button[aria-label="Accept"]',
    '#onetrust-accept-btn-handler',
]


def _build_wiki_slug(name: str) -> str:
    """Construye slug compatible con URLs de Wookieepedia."""
    return quote(name.strip().replace(' ', '_'), safe='_/:')


def _clean_description(text: str) -> str:
    """Limpia texto de descripción de referencias y espacios."""
    if "If you want to create a new article" in text or "doesn't have an article" in text:
        return ""
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class WookieepediaScraper(BasePlaywrightScraper):
    """
    Scraper de Wookieepedia usando la base de Playwright.
    Implementa selectores específicos de Fandom/Wookieepedia.
    """

    CONSENT_SELECTORS = _WOOKIEEEPEDIA_CONSENT_SELECTORS

    def _build_url(self, name: str) -> str:
        """Construye URL de Wookieepedia."""
        slug = _build_wiki_slug(name)
        return f'{settings.wookieepedia_base_url}/{slug}'

    async def _extract_description(self, page: Page, character_name: str) -> str:
        """
        Extrae primer párrafo válido probando selectores en cascada.
        Retorna el primer párrafo con >80 caracteres.
        """
        for selector in _CONTENT_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    text = (await el.inner_text()).strip()
                    cleaned = _clean_description(text)
                    if len(cleaned) > 80:
                        logger.debug(f'{character_name!r}: Encontrado con "{selector}"')
                        return cleaned
            except Exception:
                continue
        return ''

    async def scrape_series_characters(self, series_slug: str) -> list[str]:
        """
        Extrae lista de nombres de personajes de una serie desde Wookieepedia.

        Busca en la sección 'Appearances' de la página de la serie.
        Retorna lista de nombres de personajes.
        """
        # Mapeo de slugs a páginas de series en Wookieepedia
        SERIES_PAGE_MAP = {
            'ahsoka': 'Ahsoka_(television_series)',
            'the-mandalorian': 'The_Mandalorian',
            'andor': 'Andor_(television_series)',
            'obi-wan-kenobi': 'Obi-Wan_Kenobi_(television_series)',
            'the-book-of-boba-fett': 'The_Book_of_Boba_Fett',
            'the-clone-wars': 'Star_Wars:_The_Clone_Wars',
            'star-wars-rebels': 'Star_Wars_Rebels',
            'the-bad-batch': 'Star_Wars:_The_Bad_Batch',
            'the-acolyte': 'The_Acolyte',
            'star-wars-skeleton-crew': 'Star_Wars:_Skeleton_Crew',
        }

        page_name = SERIES_PAGE_MAP.get(series_slug, series_slug.replace('-', '_'))
        url = f"{settings.wookieepedia_base_url}/{page_name}"
        logger.info(f"[Wookieepedia] Scrapeando serie: {url}")

        # Crear browser con headless=False para evadir Cloudflare
        from playwright.async_api import async_playwright
        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = await browser.new_page()
        character_names = []

        try:
            # Headers más realistas para evadir Cloudflare
            await page.set_extra_http_headers({
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.9',
            })

            await page.goto(
                url,
                wait_until='networkidle',
                timeout=60000,
            )
            await asyncio.sleep(4)  # Esperar resolución de Cloudflare
            await self._dismiss_consent(page)

            # Buscar la sección de personajes (Appearances o Characters)
            # Wookieepedia usa diferentes estructuras según la serie
            selectors = [
                # Tablas scrollbox (muy común en Wookieepedia para appearances)
                'table.scrollbox a',
                'div.scrollbox a',
                '.scrollbox a',
                # Tablas de appearances
                'table.appearances td a',
                'table.appearances a',
                # Secciones con data-source
                'section[data-source="appearances"] a',
                'section[data-source="characters"] a',
                # Contenido después de headers
                'h2:has-text("Appearances") ~ div a',
                'h2:has-text("Characters") ~ div a',
                'h2:has-text("Appearances") ~ ul li a',
                'h2:has-text("Characters") ~ ul li a',
                # Divs con clase appearances
                '.mw-parser-output .appearances a',
                '.appearances a',
                # Links en tablas generales
                'table td a',
                # Secciones de cast/starring
                'h3:has-text("Starring") ~ ul li a',
                'h3:has-text("Cast") ~ ul li a',
            ]

            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        href = await el.get_attribute('href')
                        text = await el.inner_text()
                        if href and '/wiki/' in href and text:
                            name = text.strip()
                            # Filtrar: ignorar categorías, archivos, y links vacíos
                            if not name or name.startswith(('File:', 'Category:', 'Template:', 'Wookieepedia:')):
                                continue
                            # Ignorar links a episodios, películas, libros (contienen ciertas palabras)
                            lower_href = href.lower()
                            if any(x in lower_href for x in ['/episode', '/film', '/book', '/novel', '/comic', '/game']):
                                continue
                            # Ignorar si es muy largo (probablemente no es un nombre)
                            if len(name) > 60:
                                continue
                            if name not in character_names:
                                character_names.append(name)
                                logger.debug(f"Encontrado personaje: {name}")
                except Exception:
                    continue

            logger.info(f"[Wookieepedia] Serie '{series_slug}': {len(character_names)} personajes encontrados")
            return character_names

        except Exception as exc:
            logger.warning(f"[Wookieepedia] Error scrapeando serie {series_slug}: {exc}")
            return []
        finally:
            await page.close()
            await browser.close()
            await p.stop()
