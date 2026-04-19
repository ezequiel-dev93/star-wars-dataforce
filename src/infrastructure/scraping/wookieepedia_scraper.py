from __future__ import annotations
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
