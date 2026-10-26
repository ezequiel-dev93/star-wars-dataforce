# Arquitectura — Star Wars Dataforce

## Visión General

**Star Wars Dataforce** sigue **Clean Architecture (Puertos y Adaptadores)** + **SOLID** para garantizar que el pipeline ETL y CLI de scraping sea flexible, testeable y extensible sin acoplar las reglas de negocio del dominio a librerías externas de red, scraping o almacenamiento.

## Estructura de Capas

```text
main.py (CLI Entry Point: series, list-series, download-images, clean-duplicates, enrich)
├── src/application/
│   ├── use_cases/
│   │   ├── extract_databank_series.py       (Extracción por serie/película + imágenes + merge)
│   │   ├── enrich_descriptions_pipeline.py  (Enriquecimiento concurrente de biografías)
│   │   ├── extract_swapi_pipeline.py        (Pipeline base SWAPI + SwapiMapper + Pydantic)
│   │   └── extract_characters.py            (Caso de uso de ingesta HTTP)
│   ├── mappers/
│   │   └── swapi_mapper.py                  (Traducción de esquemas y resolución de URLs SWAPI)
│   └── services/
│       └── deduplication_service.py         (Deduplicación y fusión inteligente por slug)
├── src/infrastructure/
│   ├── scraping/
│   │   ├── starwars_databank_scraper.py     (Scrapling: Fetcher + StealthyFetcher WAF bypass)
│   │   ├── wookieepedia_scraper.py          (Playwright: Headless fallback scraper)
│   │   ├── base_playwright_scraper.py       (Clase base de ciclo de vida Playwright)
│   │   └── composite_scraper.py             (Patrón Composite para múltiples fuentes de scraping)
│   ├── http/
│   │   └── swapi_client.py                  (httpx: Cliente asíncrono SWAPI)
│   ├── storage/
│   │   └── image_downloader.py              (httpx: Descarga asíncrona HD + filtro anti-animación)
│   └── persistence/
│       └── json_storage.py                  (Lectura/Escritura validada de characters.json)
├── src/core/                                ← Capa más interna (Dominio puro)
│   ├── entities/character.py                (CharacterEntity, PhysicalTraits, BirthInfo, DeathInfo)
│   ├── ports/character_repository.py        (ABC para clientes de datos)
│   └── ports/scraper_port.py                (ABC para motores de scraping)
└── src/config/
    ├── settings.py                          (Pydantic Settings / Variables .env)
    ├── series_characters.py                 (Catálogo Live-Action, Animadas curadas y Clones)
    └── logging/logger.py                    (Configuración de logs con Rich)
```

## Regla de Dependencia

Las capas internas **nunca** conocen ni importan de las capas externas:

```text
core/  <──  application/  <──  infrastructure/
```

## Principios SOLID Aplicados

| Principio | Aplicación en el Proyecto |
|---|---|
| **S — Single Responsibility** | `StarWarsDatabankScraper` solo extrae fichas del Databank; `ImageDownloader` solo gestiona la descarga y caché de imágenes; `deduplication_service` solo fusiona entidades. |
| **O — Open/Closed** | Se pueden añadir nuevos scrapers (implementando `ScraperPort`) o nuevas producciones en `series_characters.py` sin modificar la lógica de los casos de uso. |
| **L — Liskov Substitution** | `StarWarsDatabankScraper`, `WookieepediaScraper` o cualquier mock de test son intercambiables donde se espera `ScraperPort`. |
| **I — Interface Segregation** | Puertos separados y específicos para repositorios de datos (`CharacterRepositoryPort`) y motores de scraping (`ScraperPort`). |
| **D — Dependency Inversion** | Los casos de uso (`EnrichDescriptionsPipelineUseCase`, `ExtractDatabankSeriesUseCase`) dependen de abstracciones y reciben sus adaptadores por inyección de dependencias. |

## Flujo Principal de Datos (Extracción de Series y Películas)

```text
Catálogo (series_characters.py)
       │
       ▼
ExtractDatabankSeriesUseCase
       │
       ├──> 1. StarWarsDatabankScraper (Scrapling: Fetcher / StealthyFetcher)
       │         └── Fallback biografía ──> WookieepediaScraper (Playwright)
       │
       ├──> 2. Reglas de Dominio / Enriquecimiento
       │         ├── Detección de Soldados Clones (is_clone_character)
       │         └── Protección de retratos Live-Action vs Animación
       │
       ├──> 3. ImageDownloader (httpx + Semaphore)
       │         └── Optimización URL Lumiere HD ──> output/images/characters/{slug}.jpg
       │
       ├──> 4. CharacterEntity (Validación estricta con Pydantic v2)
       │
       ├──> 5. deduplicate_and_merge_characters (Smart Merge con registros previos)
       │
       └──> 6. JsonStorage ──> output/characters.json
```
