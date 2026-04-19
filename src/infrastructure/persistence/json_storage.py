from __future__ import annotations
import json
from pathlib import Path
from src.core.entities.character import CharacterEntity
from src.config.settings import settings
from src.config.logging.logger import get_logger

logger = get_logger(__name__)

class JsonStorage:
    def __init__(self, output_path: Path | None = None) -> None:
        self.output_path = output_path or settings.output_path

    def write(self, characters: list[CharacterEntity]) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [c.model_dump(mode='json') for c in characters]
        with self.output_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f'[bold green]Output:[/] {len(characters)} personajes en [cyan]{self.output_path}[/]')
        return self.output_path

    def read(self) -> list[CharacterEntity]:
        if not self.output_path.exists():
            logger.warning(f'El archivo [cyan]{self.output_path}[/] no existe. Devolviendo lista vacia.')
            return []
            
        with self.output_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            
        characters = [CharacterEntity.model_validate(item) for item in data]
        logger.info(f'Cargados [bold green]{len(characters)}[/] personajes desde [cyan]{self.output_path}[/].')
        return characters
