from __future__ import annotations
import logging
from rich.logging import RichHandler
from rich.console import Console
console = Console()

def get_logger(name: str) -> logging.Logger:
    from src.config.settings import settings
    
    logging.basicConfig(
        level=settings.log_level.upper(), format='%(message)s', datefmt='[%X]',
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=True, markup=True)],
        force=True)
    return logging.getLogger(name)
