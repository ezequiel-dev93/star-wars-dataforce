from src.infrastructure.scraping.base_playwright_scraper import BasePlaywrightScraper
from src.infrastructure.scraping.wookieepedia_scraper import WookieepediaScraper
from src.infrastructure.scraping.starwars_databank_scraper import StarWarsDatabankScraper
from src.infrastructure.scraping.composite_scraper import CompositeScraper

__all__ = [
    'BasePlaywrightScraper',
    'WookiepediaScraper',
    'StarWarsDatabankScraper',
    'CompositeScraper',
]
