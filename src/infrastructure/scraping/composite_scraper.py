from __future__ import annotations
from src.core.ports.scraper_port import ScraperPort
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


class CompositeScraper(ScraperPort):
    """
    Scraper compuesto que intenta multiples fuentes en orden.
    
    Si la primera fuente no retorna descripcion (o es muy corta),
    intenta con la siguiente hasta agotar las fuentes.
    
    Ejemplo:
        primary = StarWarsDatabankScraper()      # Oficial
        fallback = WookieepediaScraper()         # Comunidad
        scraper = CompositeScraper([primary, fallback])
    """

    def __init__(
        self,
        scrapers: list[ScraperPort],
        min_description_length: int = 80,
        source_prefix: bool = False
    ) -> None:
        """
        Args:
            scrapers: Lista de scrapers a probar en orden
            min_description_length: Longitud minima para considerar valida una descripcion
            source_prefix: Si True, agrega prefijo indicando la fuente (debug)
        """
        self._scrapers = scrapers
        self._min_length = min_description_length
        self._source_prefix = source_prefix

    async def scrape_description(self, character_name: str) -> str:
        """
        Intenta scrapear de cada fuente en orden hasta obtener resultado valido.
        
        Returns:
            Descripcion del personaje o string vacio si ninguna fuente la tiene.
        """
        for idx, scraper in enumerate(self._scrapers, 1):
            try:
                logger.debug(
                    f"{character_name!r}: Intentando fuente {idx}/{len(self._scrapers)}"
                )
                description = await scraper.scrape_description(character_name)
                
                if description and len(description) >= self._min_length:
                    source_name = scraper.__class__.__name__.replace('Scraper', '')
                    logger.info(
                        f"{character_name!r}: Descripcion encontrada en {source_name} "
                        f"({len(description)} caracteres)"
                    )
                    
                    if self._source_prefix:
                        return f"[{source_name}] {description}"
                    return description
                
                logger.debug(
                    f"{character_name!r}: Fuente {idx} no retorno descripcion valida"
                )
                
            except Exception as exc:
                logger.warning(
                    f"{character_name!r}: Error en fuente {idx}: {exc}"
                )
                continue
        
        logger.warning(
            f"{character_name!r}: No se encontro descripcion en ninguna fuente"
        )
        return ""

    async def close(self) -> None:
        # Cierra todos los scrapers.
        for scraper in self._scrapers:
            try:
                await scraper.close()
            except Exception as exc:
                logger.debug(f"Error cerrando scraper: {exc}")

    async def __aenter__(self) -> 'CompositeScraper':
        for scraper in self._scrapers:
            if hasattr(scraper, '_ensure_browser'):
                await scraper._ensure_browser()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
