"""
Script para debuggear el scraper del Databank - guarda el HTML.

Uso:
    uv run python scripts/debug_databank.py "din-djarin"
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright


async def main() -> None:
    slug = sys.argv[1] if len(sys.argv) > 1 else "din-djarin"
    url = f"https://www.starwars.com/databank/{slug}"

    print(f"Navegando a: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # Guardar HTML
        html = await page.content()
        output_file = Path("databank_debug.html")
        output_file.write_text(html, encoding="utf-8")
        print(f"HTML guardado en: {output_file.absolute()}")

        # Intentar extraer título
        title_el = await page.query_selector('h1')
        if title_el:
            title = await title_el.inner_text()
            print(f"Título encontrado: {title}")
        else:
            print("No se encontró h1")

        # Intentar extraer párrafos
        paragraphs = await page.query_selector_all('p')
        print(f"\nPrimeros 3 párrafos:")
        for i, p in enumerate(paragraphs[:3]):
            text = await p.inner_text()
            print(f"  {i+1}. {text[:100]}...")

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
