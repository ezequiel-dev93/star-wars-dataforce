from __future__ import annotations
import json
from pathlib import Path
from src.core.entities.character import CharacterEntity
from src.shared.config.settings import settings
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)

class JsonWriter:
    def __init__(self, output_path: Path | None = None) -> None:
        self.output_path = output_path or settings.output_path

    def write(self, characters: list[CharacterEntity]) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [c.model_dump(mode='json') for c in characters]
        with self.output_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f'[bold green]Output:[/] {len(characters)} personajes en [cyan]{self.output_path}[/]')
        return self.output_path
