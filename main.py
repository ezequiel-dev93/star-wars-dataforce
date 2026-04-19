from __future__ import annotations
import asyncio
import argparse
import sys

from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper
from src.application.use_cases.enrich_descriptions_pipeline import EnrichDescriptionsPipelineUseCase
from src.application.use_cases.extract_databank_series import ExtractDatabankSeriesUseCase
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


async def enrich_with_databank() -> None:
    """Modo: Enriquecer descripciones faltantes en characters.json usando Databank."""
    logger.info('[bold blue]== Modo Enriquecimiento: Databank ==[/]')

    async with StarWarsDatabankScraper(headless=False) as scraper:
        pipeline = EnrichDescriptionsPipelineUseCase(scraper)
        output = await pipeline.execute()

    logger.info(f'[bold]Resultado guardado en:[/] [cyan]{output}[/]')


async def extract_series(series_slug: str) -> None:
    """Modo: Extraer personajes nuevos de una serie específica del Databank."""
    logger.info(f'[bold blue]== Extrayendo serie: {series_slug} ==[/]')

    use_case = ExtractDatabankSeriesUseCase()
    output = await use_case.execute(series_slug)

    logger.info(f'[bold]Resultado guardado en:[/] [cyan]{output}[/]')


async def extract_multiple_series(series_list: list[str]) -> None:
    """Modo: Extraer personajes de múltiples series."""
    logger.info(f'[bold blue]== Extrayendo {len(series_list)} series ==[/]')

    use_case = ExtractDatabankSeriesUseCase()
    output = await use_case.execute_multiple(series_list)

    logger.info(f'[bold]Resultado guardado en:[/] [cyan]{output}[/]')


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Star Wars Dataforce - ETL Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Enriquecer descripciones faltantes
  uv run python main.py enrich

  # Extraer personajes de The Mandalorian
  uv run python main.py series the-mandalorian

  # Extraer múltiples series
  uv run python main.py series the-mandalorian andor obi-wan-kenobi
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')

    # Comando: enrich
    enrich_parser = subparsers.add_parser('enrich', help='Enriquecer descripciones faltantes')

    # Comando: series
    series_parser = subparsers.add_parser('series', help='Extraer personajes de serie(s)')
    series_parser.add_argument(
        'slugs',
        nargs='+',
        help='Slug(s) de la(s) serie(s) (ej: the-mandalorian, andor, obi-wan-kenobi)'
    )

    # Comando: list-series (para ver series disponibles)
    list_parser = subparsers.add_parser('list-series', help='Listar series populares disponibles')

    args = parser.parse_args()

    if args.command == 'enrich':
        asyncio.run(enrich_with_databank())
        return 0

    elif args.command == 'series':
        if len(args.slugs) == 1:
            asyncio.run(extract_series(args.slugs[0]))
        else:
            asyncio.run(extract_multiple_series(args.slugs))
        return 0

    elif args.command == 'list-series':
        print("""
Series disponibles en StarWars.com Databank:
  - the-mandalorian          (The Mandalorian)
  - the-book-of-boba-fett    (The Book of Boba Fett)
  - obi-wan-kenobi           (Obi-Wan Kenobi)
  - andor                    (Andor)
  - ahsoka                   (Ahsoka)
  - the-acolyte              (The Acolyte)
  - star-wars-skeleton-crew  (Skeleton Crew)
  - star-wars-rebels         (Star Wars Rebels)
  - the-bad-batch            (The Bad Batch)
  - the-clone-wars           (The Clone Wars)
  - resistance               (Star Wars Resistance)

Para extraer:
  uv run python main.py series the-mandalorian
        """)
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
