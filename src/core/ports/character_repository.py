from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class CharacterRepositoryPort(ABC):
    @abstractmethod
    async def fetch_all(self) -> list[dict[str, Any]]: ...
    @abstractmethod
    async def fetch_by_id(self, character_id: int) -> dict[str, Any] | None: ...
