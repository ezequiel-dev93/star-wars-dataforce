# Star Wars Dataforce

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-success.svg)](docs/ARCHITECTURE.md)
[![SOLID](https://img.shields.io/badge/Design-SOLID-brightgreen.svg)]()

## Descripción

**Star Wars Dataforce** es un pipeline ETL (Extract, Transform, Load) y CLI de scraping asíncrono construido en Python. Su objetivo es consolidar, enriquecer y deduplicar datos del universo Star Wars provenientes de múltiples fuentes (StarWars.com Databank, Wookieepedia y SWAPI), unificándolos en un único dataset curado con retratos en alta resolución.

Desarrollado aplicando **Clean Architecture (Puertos y Adaptadores) y principios SOLID**, el proyecto prioriza la mantenibilidad, el bajo acoplamiento y la facilidad para realizar pruebas unitarias (*testability*).

## Features

* **Web Scraping Evasivo con Scrapling:** Extracción rápida y *stealth* desde **StarWars.com Databank** mediante `Scrapling` (`Fetcher` / `StealthyFetcher` con fingerprinting TLS y evasión de WAF Akamai/Cloudflare), con fallback automático a **Wookieepedia** (`Playwright`).
* **Catálogo Curado Live-Action y Animación:** Extracción selectiva de películas, series *Live-Action* (Mandalorian, Andor, Ahsoka, The Acolyte, Skeleton Crew, etc.) y series animadas curadas (*The Clone Wars*, *The Bad Batch*, *Star Wars Rebels*, *Star Wars Resistance*).
* **Descarga Inteligente de Imágenes HD:** Descargador asíncrono (`ImageDownloader`) que optimiza URLs del CDN de Disney/Lumiere para máxima resolución, evita re-descargas por caché local y protege retratos *Live-Action* frente a ilustraciones animadas.
* **Deduplicación y Fusión (Smart Merge):** Servicio de dominio/aplicación que unifica personajes repetidos por `slug`, combinando apariciones, afiliaciones, planetas, especies y seleccionando automáticamente la descripción más rica y completa.
* **Detección Automática de Clones:** Reglas de negocio para identificar soldados clones de la República (`Clone Troopers`) y enriquecer sus afiliaciones y especie automáticamente.
* **Validación Estricta:** Esquemas `Pydantic v2` (`CharacterEntity`) como capa anticorrupción antes de persistir en JSON.

## Stack Tecnológico

* **Lenguaje:** Python 3.12+ (gestionado con `uv` para resolución de dependencias ultrarrápida).
* **Core / Arquitectura:** Clean Architecture, Puertos y Adaptadores, SOLID, Inyección de Dependencias.
* **Scraping & Extracción (I/O):** `scrapling[all]` (Stealth TLS Scraping), `playwright` (Async Headless Fallback), `httpx` (Async HTTP & Image Downloader).
* **Transformación & Validación:** `pydantic v2` (validación, coerción de tipos y limpieza declarativa), `pydantic-settings`, Data Mappers (`SwapiMapper`) y servicios de fusión en memoria.
* **Testing & CLI:** `pytest` (`pytest-asyncio`), `argparse`, `rich` (Logging visual y barras de progreso).

## Decisiones Técnicas

* **Clean Architecture & Puertos y Adaptadores:** Se definieron contratos abstractos en la capa `core` (`CharacterRepositoryPort`, `ScraperPort`) para que los casos de uso no conozcan detalles de implementación de `Scrapling`, `Playwright` o `httpx`.
* **Estrategia Híbrida de Scraping (`Scrapling` + `Playwright`):** Para evitar el costo de levantar navegadores completos en cada ficha y sortear protecciones anti-bot en StarWars.com Databank, se adoptó `Scrapling` con fallback a `StealthyFetcher`, delegando a `WookieepediaScraper` únicamente cuando una biografía requiere enriquecimiento adicional.
* **Regla de Oro para Retratos (Live-Action First):** Si un personaje ya existe en el catálogo con fotografía *Live-Action*, el pipeline bloquea el reemplazo de su avatar por ilustraciones de series animadas, permitiendo imágenes animadas únicamente para personajes exclusivos de animación.
* **Deduplicación Incremental Idempotente:** Cada ejecución del pipeline sobre nuevas series fusiona sin pérdida de datos (`deduplicate_and_merge_characters`) las listas de apariciones, planetas y rasgos físicos, re-secuenciando los IDs del dataset.

## 🛠 Instalación y Uso (CLI)

*Requisito previo: Tener instalado el gestor de paquetes `uv`.*

```bash
# 1. Instalar dependencias del proyecto de forma sincronizada
uv sync

# 2. Instalar navegadores requeridos por Playwright / Scrapling
uv run playwright install chromium
```

### Comandos Disponibles

```bash
# Ver ayuda general de la CLI
uv run python main.py --help

# 1. Listar producciones Live-Action y series animadas curadas disponibles
uv run python main.py list-series

# 2. Extraer personajes de una o más producciones (películas o series)
uv run python main.py series the-mandalorian andor ahsoka
uv run python main.py series the-clone-wars the-bad-batch star-wars-rebels

# 3. Descargar imágenes HD pendientes para personajes en characters.json
uv run python main.py download-images
uv run python main.py download-images --limit 25

# 4. Limpiar y fusionar personajes duplicados en output/characters.json
uv run python main.py clean-duplicates

# 5. Enriquecer descripciones faltantes de manera concurrente
uv run python main.py enrich
```

> **Nota:** El dataset consolidado se guarda en `output/characters.json` y los retratos en `output/images/characters/`.

### Ejecutar Tests

```bash
uv run pytest tests/unit/ -v
```

## Variables de Entorno (.env)

El proyecto es parametrizable mediante un archivo `.env` validado con `pydantic-settings`:

| Variable | Default | Descripción |
|---|---|---|
| `STARWARS_DATABANK_BASE_URL` | `https://www.starwars.com/databank` | URL base del Databank oficial de Star Wars |
| `DATABANK_SCRAPING_ENABLED` | `true` | Habilita el scraping desde StarWars.com Databank |
| `WOOKIEEPEDIA_BASE_URL` | `https://starwars.fandom.com/wiki` | URL base de Wookieepedia para fallback |
| `SWAPI_BASE_URL` | `https://swapi.dev/api` | URL base del proveedor SWAPI |
| `SCRAPING_CONCURRENCY` | `5` | Límite de tareas concurrentes (Semáforo) |
| `SCRAPING_HEADLESS` | `true` | Ejecución sin ventana gráfica para navegadores |
| `OUTPUT_PATH` | `output/characters.json` | Ruta del archivo JSON consolidado |
| `LOG_LEVEL` | `INFO` | Nivel de salida del logger enriquecido con `rich` |

## Próximas Mejoras (Roadmap)

* **Independencia de Datos (Migración a Supabase):** El objetivo principal de este pipeline ETL es extraer, curar y validar la información e imágenes para **poblar una base de datos propia en Supabase** que alimente la API de *Star Wars Holocron*, contando con un *Single Source of Truth* propio del ecosistema Star Wars.
* **Observabilidad y Métricas:** Reportes detallados de cobertura de campos y tiempos de extracción por fuente.
* **Integración Continua (CI):** Workflows de GitHub Actions para ejecutar `ruff`, `mypy`/`pyright` y `pytest` en cada Pull Request.
