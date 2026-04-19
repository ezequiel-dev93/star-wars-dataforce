from __future__ import annotations
from typing import Any
from src.core.ports.character_repository import CharacterRepositoryPort
from src.config.logging.logger import get_logger

logger = get_logger(__name__)

class ExtractCharactersUseCase:
    def __init__(self, repository: CharacterRepositoryPort) -> None:
        self._repository = repository

    async def execute(self) -> list[dict[str, Any]]:
        logger.info('Extrayendo personajes...')
        data = await self._repository.fetch_all()
        logger.info(f'[bold]{len(data)}[/] personajes extraidos.')
        return data
