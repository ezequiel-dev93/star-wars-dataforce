"""
Script para extraer personajes de The Mandalorian desde StarWars.com Databank.

Uso:
    uv run python scripts/extract_mandalorian.py
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# Agregar raiz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.use_cases.extract_databank_series import ExtractDatabankSeriesUseCase


async def main() -> None:
    """Extrae personajes de The Mandalorian."""
    use_case = ExtractDatabankSeriesUseCase()
    output_path = await use_case.execute('the-mandalorian')
    print(f"\nOutput saved to: {output_path}")


if __name__ == '__main__':
    asyncio.run(main())
