# Arquitectura — Star Wars Dataforce

## Vision General

Star Wars Dataforce sigue **Clean Architecture** + **SOLID** para garantizar que el
pipeline ETL sea flexible, testeable y extensible sin acoplar el dominio a los frameworks.

## Capas

`
main.py (Entry Point)
    └── application/use_cases/
            BuildCharacterPipeline | ExtractCharacters | ScrapeDescriptions
                ├── infrastructure/
                │       SwapiClient (httpx)
                │       WookiepediaScraper (playwright)
                │       JsonWriter
                ├── transformation/
                │       CharacterCleaner (pandas)
                │       CharacterMerger (pandas)
                └── src/core/                  ← Capa mas interna
                        entities/CharacterEntity (pydantic)
                        ports/CharacterRepositoryPort (ABC)
                        ports/ScraperPort (ABC)
shared/
    config/Settings | logging/get_logger
`

## Regla de Dependencia

Las capas internas NUNCA importan de las externas:

`
core/ <- application/ <- infrastructure/
core/ <- application/ <- transformation/
`

## Principios SOLID

| Principio | Aplicacion |
|---|---|
| S - Single Responsibility | SwapiClient solo hace HTTP. CharacterCleaner solo limpia. |
| O - Open/Closed | Agregar un nuevo cliente sin tocar los use cases. |
| L - Liskov Substitution | Cualquier mock de CharacterRepositoryPort es intercambiable. |
| I - Interface Segregation | Puertos separados para HTTP y Scraping. |
| D - Dependency Inversion | Use cases dependen de ports (ABC), no de httpx ni playwright. |

## Flujo de Datos

`
SWAPI ──> SwapiClient ──> ExtractCharactersUseCase
                                    |
                         CharacterCleaner (pandas)
                                    |
Wookieepedia ──> WookiepediaScraper ──> ScrapeDescriptionsUseCase
                                    |
                         CharacterMerger (pandas)
                                    |
                     CharacterEntity (pydantic validation)
                                    |
                      JsonWriter ──> output/characters.json
`
