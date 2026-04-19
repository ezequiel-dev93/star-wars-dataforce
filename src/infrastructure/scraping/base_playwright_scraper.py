from __future__ import annotations
from abc import abstractmethod
from typing import ClassVar
from playwright.async_api import async_playwright, Browser, Page
from src.core.ports.scraper_port import ScraperPort
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


class BasePlaywrightScraper(ScraperPort):
    """
    Clase base para scrapers que usan Playwright.
    Centraliza la gestión del browser, consent banners y ciclo de vida.

    Las subclases deben implementar:
    - CONSENT_SELECTORS: selectores para cerrar banners de cookies
    - _build_url(): construir URL a partir del nombre
    - _extract_description(): lógica específica de extracción
    """

    CONSENT_SELECTORS: ClassVar[list[str]] = [
        '[data-tracking-opt-in-accept]',
        '#onetrust-accept-btn-handler',
        'button[aria-label*="Accept"]',
    ]

    def __init__(self, headless: bool | None = None) -> None:
        """
        Args:
            headless: Si None, usa el valor de settings.scraping_headless
        """
        self._playwright = None
        self._browser: Browser | None = None
        self._headless = headless if headless is not None else settings.scraping_headless

    async def _ensure_browser(self) -> Browser:
        # Inicializa el browser de Playwright si no existe.
        if self._browser is None:
            self._playwright = await async_playwright().start()
            args = ['--disable-blink-features=AutomationControlled']
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                args=args,
            )
        return self._browser

    async def _dismiss_consent(self, page: Page) -> None:
        # Intenta cerrar banners de cookies/GDPR.
        for selector in self.CONSENT_SELECTORS:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2_000):
                    await btn.click(timeout=2_500)
                    await page.wait_for_timeout(500)
                    logger.debug(f'{self.__class__.__name__}: Consent banner dismissed')
                    return
            except Exception:
                continue

    @abstractmethod
    def _build_url(self, name: str) -> str:
        # Construye la URL completa para el personaje.
        ...

    @abstractmethod
    async def _extract_description(self, page: Page, character_name: str) -> str:
        # Extrae la descripción de la página cargada.
        ...

    async def scrape_description(self, character_name: str) -> str:
        # Template method para scrapear descripción.
        # Las subclases pueden sobreescribir para comportamiento específico.
        browser = await self._ensure_browser()
        url = self._build_url(character_name)

        page = await browser.new_page()
        try:
            await page.set_extra_http_headers({
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.5',
            })

            await page.goto(
                url,
                wait_until='networkidle',
                timeout=settings.scraping_page_timeout_ms,
            )
            await self._dismiss_consent(page)

            return await self._extract_description(page, character_name)

        except Exception as exc:
            logger.warning(f'{self.__class__.__name__}: Error scraping {character_name!r}: {exc}')
            return ''
        finally:
            await page.close()

    async def close(self) -> None:
        # Cierra el browser y libera recursos.
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = self._playwright = None

    async def __aenter__(self) -> 'BasePlaywrightScraper':
        await self._ensure_browser()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
