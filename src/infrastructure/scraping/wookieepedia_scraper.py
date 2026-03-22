from __future__ import annotations
from playwright.async_api import async_playwright, Browser, Page
from src.core.ports.scraper_port import ScraperPort
from src.shared.config.settings import settings
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)
_SELECTOR = '.mw-parser-output > p:not(.quote)'

class WookiepediaScraper(ScraperPort):
    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=settings.scraping_headless)
        return self._browser

    async def scrape_description(self, character_name: str) -> str:
        browser = await self._ensure_browser()
        page: Page = await browser.new_page()
        slug = character_name.replace(' ', '_')
        url = f'{settings.wookieepedia_base_url}/{slug}'
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20_000)
            await page.wait_for_selector(_SELECTOR, timeout=8_000)
            for p in await page.query_selector_all(_SELECTOR):
                text = (await p.inner_text()).strip()
                if len(text) > 80:
                    return text
            return ''
        except Exception as exc:
            logger.warning(f'Error scrapeando {character_name!r}: {exc}')
            return ''
        finally:
            await page.close()

    async def close(self) -> None:
        if self._browser: await self._browser.close()
        if self._playwright: await self._playwright.stop()
        self._browser = self._playwright = None

    async def __aenter__(self) -> 'WookiepediaScraper':
        await self._ensure_browser()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
