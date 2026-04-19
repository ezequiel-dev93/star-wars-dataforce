from __future__ import annotations
import asyncio
from typing import Sequence
from pathlib import Path
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn,
)

from src.core.entities.character import CharacterEntity
from src.core.ports.scraper_port import ScraperPort
from src.infrastructure.persistence.json_storage import JsonStorage
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)

class EnrichDescriptionsPipelineUseCase:
    """
    Lee personajes desde el almacenamiento local, busca descripciones faltantes 
    usando un scraper (ej. Databank o Wookieepedia) de forma concurrente, 
    y guarda los personajes actualizados.
    """

    def __init__(self, scraper: ScraperPort, storage: JsonStorage | None = None) -> None:
        self._scraper = scraper
        self._storage = storage or JsonStorage()

    async def execute(self) -> Path:
        logger.info('[bold blue]== Iniciando Enriquecimiento de Descripciones ==[/]')
        
        # 1. Leer personajes guardados
        characters = self._storage.read()
        if not characters:
            logger.error('No se encontraron personajes para enriquecer. Corre el pipeline de extraccion primero.')
            return self._storage.output_path

        # 2. Identificar faltantes
        to_enrich = [c for c in characters if not c.description]
        already_enriched = len(characters) - len(to_enrich)
        
        logger.info(f'[bold green]{already_enriched}[/] personajes ya tienen descripcion.')
        
        if not to_enrich:
            logger.info('Todos los personajes tienen descripcion. Pipeline finalizado.')
            return self._storage.output_path
            
        logger.info(f'[bold yellow]{len(to_enrich)}[/] personajes necesitan descripcion.')

        # 3. Scrapear de manera concurrente
        semaphore = asyncio.Semaphore(settings.scraping_concurrency)
        found = 0

        async def scrape_and_update(char: CharacterEntity, progress: Progress, task_id) -> None:
            nonlocal found
            async with semaphore:
                progress.update(task_id, description=f'[cyan]{char.name}[/]')
                desc = await self._scraper.scrape_description(char.name)
                if desc:
                    char.description = desc
                    found += 1
                progress.advance(task_id)

        with Progress(
            SpinnerColumn(),
            TextColumn('[bold blue]Scraping[/] {task.description}'),
            BarColumn(bar_width=30),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task('Iniciando...', total=len(to_enrich))
            tasks = [scrape_and_update(c, progress, task_id) for c in to_enrich]
            await asyncio.gather(*tasks)

        # 4. Guardar resultados
        empty_now = len(to_enrich) - found
        logger.info(
            f'[bold green]Enriquecimiento completo:[/] '
            f'[green]{found}[/] nuevas descripciones encontradas | '
            f'[yellow]{empty_now}[/] siguen sin descripcion.'
        )
        
        output_path = self._storage.write(characters)
        return output_path
