"""
Star Wars Dataforce - CLI Principal de ETL y Scraping.

Comandos:
  clean-duplicates : Limpia y fusiona personajes repetidos en characters.json
  download-images  : Descarga imágenes de alta resolución pendientes para los personajes
  series           : Extrae producciones Live-Action usando Scrapling y descarga sus imágenes
  list-series      : Lista las series Live-Action disponibles y señala las animadas excluidas
  enrich           : Enriquecer descripciones faltantes
"""
from __future__ import annotations
import asyncio
import argparse
import sys
from pathlib import Path

from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper
from src.infrastructure.storage.image_downloader import ImageDownloader
from src.infrastructure.persistence.json_storage import JsonStorage
from src.application.services.deduplication_service import deduplicate_and_merge_characters
from src.application.use_cases.extract_databank_series import ExtractDatabankSeriesUseCase
from src.application.use_cases.enrich_descriptions_pipeline import EnrichDescriptionsPipelineUseCase
from src.config.series_characters import (
    LIVE_ACTION_PRODUCTIONS,
    ANIMATED_PRODUCTIONS,
    ANIMATED_SERIES_CHARACTERS,
    list_live_action_productions,
    list_available_animated_series,
)
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


def clean_duplicates_command() -> None:
    """Ejecuta la deduplicación y fusión sobre characters.json."""
    logger.info("[bold blue]== Limpieza y Fusión de Duplicados ==[/]")
    storage = JsonStorage()
    characters = storage.read()

    before_count = len(characters)
    merged = deduplicate_and_merge_characters(characters)
    after_count = len(merged)

    output_path = storage.write(merged)
    logger.info(
        f"[bold green]Deduplicación completada con éxito:[/]\n"
        f"  - Registros antes: [yellow]{before_count}[/]\n"
        f"  - Registros después: [bold green]{after_count}[/]\n"
        f"  - Duplicados unificados: [cyan]{before_count - after_count}[/]\n"
        f"  - Archivo guardado: [cyan]{output_path}[/]"
    )


async def download_images_command(limit: int | None = None) -> None:
    """Descarga imágenes para personajes en characters.json que no tengan imagen local."""
    logger.info("[bold blue]== Descarga de Imágenes para Personajes ==[/]")
    storage = JsonStorage()
    characters = storage.read()
    downloader = ImageDownloader()
    scraper = StarWarsDatabankScraper()

    pending = []
    for c in characters:
        existing = downloader.get_existing_image(c.slug)
        if not existing:
            pending.append(c)

    logger.info(
        f"Total personajes: {len(characters)} | "
        f"Con imagen local: {len(characters) - len(pending)} | "
        f"Pendientes: [bold yellow]{len(pending)}[/]"
    )

    if not pending:
        logger.info("[bold green]¡Todos los personajes ya cuentan con imagen descargada![/]")
        return

    to_process = pending[:limit] if limit else pending
    updated_count = 0

    async with scraper:
        for idx, char in enumerate(to_process, 1):
            logger.info(f"[{idx}/{len(to_process)}] Buscando imagen para: [cyan]{char.name}[/] ({char.slug})")
            img_url = ""

            # Si ya tenía una URL web guardada, usarla
            if char.avatar_url and char.avatar_url.startswith("http"):
                img_url = char.avatar_url
            else:
                data = await scraper.scrape_character_full(char.slug)
                if data and data.image_url:
                    img_url = data.image_url

            if img_url:
                saved = await downloader.download_character_image(char.slug, img_url)
                if saved:
                    char.avatar_url = str(saved.as_posix())
                    updated_count += 1
            else:
                logger.debug(f"No se encontró URL de imagen para '{char.slug}'")

            await asyncio.sleep(0.4)

    storage.write(characters)
    logger.info(f"[bold green]Completado. {updated_count} nuevas imágenes descargadas y registradas.[/]")


async def extract_series_command(series_slugs: list[str]) -> None:
    """Extrae producciones Live-Action usando Scrapling."""
    use_case = ExtractDatabankSeriesUseCase()
    output = await use_case.execute_multiple(series_slugs)
    logger.info(f"[bold]Resultado guardado en:[/] [cyan]{output}[/]")


async def enrich_command() -> None:
    """Enriquece descripciones faltantes en characters.json."""
    scraper = StarWarsDatabankScraper()
    async with scraper:
        pipeline = EnrichDescriptionsPipelineUseCase(scraper)
        output = await pipeline.execute()
    logger.info(f"[bold]Resultado guardado en:[/] [cyan]{output}[/]")


def list_series_command() -> None:
    """Lista las producciones Live-Action y las animadas disponibles."""
    print("\n" + "=" * 60)
    print("PRODUCCIONES LIVE-ACTION DISPONIBLES:")
    print("=" * 60)
    for slug, chars in LIVE_ACTION_PRODUCTIONS.items():
        print(f"  [+] {slug:<26} ({len(chars)} personajes clave)")

    print("\n" + "=" * 60)
    print("PRODUCCIONES ANIMADAS CURADAS (DISPONIBLES):")
    print("=" * 60)
    for slug, chars in ANIMATED_SERIES_CHARACTERS.items():
        print(f"  [+] {slug:<26} ({len(chars)} personajes curados / exclusivos)")

    print("\n" + "=" * 60)
    print("OTRAS PRODUCCIONES ANIMADAS (PENDIENTES DE CURAR):")
    print("=" * 60)
    for slug in sorted(list(ANIMATED_PRODUCTIONS)):
        if slug not in ANIMATED_SERIES_CHARACTERS:
            print(f"  [-] {slug:<26} [PENDIENTE]")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Star Wars Dataforce - ETL & Scrapling Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Comando: clean-duplicates
    subparsers.add_parser("clean-duplicates", help="Limpiar y fusionar duplicados en characters.json")

    # Comando: download-images
    dl_parser = subparsers.add_parser("download-images", help="Descargar imágenes de personajes pendientes")
    dl_parser.add_argument("--limit", type=int, default=None, help="Límite máximo de imágenes a descargar")

    # Comando: series
    series_parser = subparsers.add_parser("series", help="Extraer personajes de producciones Live-Action")
    series_parser.add_argument("slugs", nargs="+", help="Slug(s) de la(s) producción(es)")

    # Comando: list-series
    subparsers.add_parser("list-series", help="Listar producciones permitidas y excluidas")

    # Comando: enrich
    subparsers.add_parser("enrich", help="Enriquecer descripciones faltantes")

    args = parser.parse_args()

    if args.command == "clean-duplicates":
        clean_duplicates_command()
        return 0
    elif args.command == "download-images":
        asyncio.run(download_images_command(limit=args.limit))
        return 0
    elif args.command == "series":
        asyncio.run(extract_series_command(args.slugs))
        return 0
    elif args.command == "list-series":
        list_series_command()
        return 0
    elif args.command == "enrich":
        asyncio.run(enrich_command())
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
