"""
Script para debuggear la página de series del Databank.

Uso:
    uv run python scripts/debug_databank_series.py
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright


async def main() -> None:
    url = "https://www.starwars.com/databank/the-mandalorian"

    print(f"Navegando a: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # Guardar HTML
        html = await page.content()
        output_file = Path("databank_series_debug.html")
        output_file.write_text(html, encoding="utf-8")
        print(f"HTML guardado en: {output_file.absolute()}")

        # Buscar enlaces a databank
        links = await page.query_selector_all('a[href*="/databank/"]')
        print(f"\nEncontrados {len(links)} enlaces a /databank/:")

        seen = set()
        for link in links[:20]:  # Primeros 20
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href and href not in seen:
                seen.add(href)
                print(f"  - {text.strip()[:50]:<50} | {href}")

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
