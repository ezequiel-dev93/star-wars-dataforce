from __future__ import annotations
from abc import ABC, abstractmethod

class ScraperPort(ABC):
    @abstractmethod
    async def scrape_description(self, character_name: str) -> str: ...
    @abstractmethod
    async def close(self) -> None: ...
