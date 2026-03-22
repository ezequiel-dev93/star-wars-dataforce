# Star Wars Dataforce

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-success.svg)](docs/ARCHITECTURE.md)
[![SOLID](https://img.shields.io/badge/Design-SOLID-brightgreen.svg)]()

## Descripción

**Star Wars Dataforce** es un pipeline ETL (Extract, Transform, Load) asíncrono construido en Python. Su objetivo es consolidar datos del universo Star Wars provenientes de múltiples fuentes incompletas, resolviendo problemas de consistencia de datos y unificándolos en un solo dataset confiable. 

El sistema extrae información estructurada mediante API (SWAPI), realiza scraping concurrente para obtener datos enriquecidos y no estructurados (Wookieepedia), limpia y unifica los conjuntos de datos, y finalmente valida exhaustivamente la salida. Desarrollado aplicando **Clean Architecture y principios SOLID**, el proyecto prioriza la mantenibilidad, el bajo acoplamiento y la facilidad para realizar pruebas unitarias (*testability*).

## Features

*   **Extracción Concurrente:** Cliente HTTP asíncrono para ingestar datos desde APIs de forma eficiente y no bloqueante.
*   **Web Scraping Resiliente:** Extracción de descripciones enriquecidas desde webs complejas mediante automatización de navegadores *headless* asíncrona.
*   **Procesamiento de Datos:** Limpieza, normalización y cruce de datos estructurados y no estructurados optimizado en memoria.
*   **Validación Estricta:** Chequeo en tiempo de ejecución de esquemas de datos complejos antes de la persistencia para garantizar calidad de datos.
*   **Diseño Desacoplado:** Arquitectura en capas que aísla la lógica core/dominio de las librerías e infraestructura externas (HTTP, Scraping, IO).

## Stack Tecnológico

*   **Lenguaje:** Python 3.12+ (gestionado con `uv` para dependencias ultrarrápidas).
*   **Core / Arquitectura:** Clean Architecture, SOLID, Inyección de Dependencias.
*   **Extracción (I/O):** `httpx` (Async HTTP), `playwright` (Async Headless Scraping).
*   **Transformación (Data):** `pandas`.
*   **Validación:** `pydantic v2`.
*   **Testing & Logging:** `pytest` (Asyncio), `rich` (Logging visual).

## Decisiones Técnicas

*   **Clean Architecture & Puertos y Adaptadores:** Se definieron interfaces (Abstract Base Classes) en la capa de dominio (`CharacterRepositoryPort`, `ScraperPort`) para que los casos de uso (`BuildCharacterPipelineUseCase`) no conozcan detalles comerciales ni de implementación de la API o el scraper. Esto es crítico para lograr que los tests de lógica de negocio se aíslen del I/O y permitir cambiar proveedores a futuro (Sustitución de Liskov).
*   **Asincronismo (Asyncio):** Dado que el cuello de botella evidente de este pipeline es de I/O (llamadas de red y renderizado de páginas pesadas), se diseñó todo el flujo de extracción en corrutinas. Esto reduce drásticamente el tiempo total de ejecución respecto a una aproximación tradicional sincrónica o basada puramente en threading.
*   **Validación Fuerte en Fronteras:** Se utilizó Pydantic v2 para funcionar como capa anticorrupción (Anti-Corruption Layer). Tras la transformación y el merge de los conjuntos de datos masivos en Pandas, se valida cada entidad resultante para garantizar que los modelos expuestos al output no propaguen nulls ni tipos erróneos.
*   **Uso de `uv`:** Se optó por el moderno gestor de paquetes de Rust, `uv`, en lugar de herramientas clásicas por su altísima velocidad en resolución de dependencias, reduciendo los tiempos de CI y setup local.

## 🛠 Instalación y Ejecución

*Requisito previo: Tener instalado el manejador de repositorios y paquetes `uv`.*

```bash
# 1. Instalar dependencias del proyecto de forma sincronizada
uv sync

# 2. Instalar binarios de navegador embebidos requeridos por Playwright
uv run playwright install chromium

# 3. Disparar ejecución del pipeline ETL completo
uv run python main.py
```
> **Nota:** El archivo final curado y validado se volcará en `output/characters.json`.

**Correr la suite de Unit Tests:**
```bash
uv run pytest tests/unit/ -v
```

## Variables de Entorno (.env)

El proyecto es totalmente parametrizable vía un archivo `.env`:

| Variable | Default | Descripción |
|---|---|---|
| `SWAPI_BASE_URL` | `https://swapi.dev/api` | Base URL del data provider principal |
| `SCRAPING_CONCURRENCY` | `5` | Límite de navegadores concurrentes (Semáforo) |
| `SCRAPING_HEADLESS` | `true` | UI flag para Playwright (false mode dev/debug) |
| `OUTPUT_PATH` | `output/characters.json` | Path de archivo consolidado |
| `LOG_LEVEL` | `INFO` | Nivel de output del sistema de logs enriquecidos |

## Aprendizajes

*   **Orquestación de Scraping Asíncrono:** Balancear la concurrencia en Playwright es fundamental; un exceso de workers puede agotar la memoria de la máquina (OOM) o desencadenar rate-limits o mecanismos anti-bot. Implementar semáforos (`asyncio.Semaphore`) y atar la concurrencia a variables de entorno resolvió el desafío adaptando el consumo a la capacidad de la infraestructura.
*   **Interoperabilidad Pandas <-> Dominio:** Interconectar de forma elegante DataFrames (optimizados para operaciones en lote) mediante adaptadores al final del proceso con validación Entity de Pydantic implicó pensar la capa de aplicación más como un orchestrador de transformadores.

## Próximas Mejoras (Roadmap)

*   **Independencia de Datos (Migración a Supabase):** SWAPI se utiliza actualmente como fuente de datos provisoria. El objetivo principal de este pipeline ETL es extraer y curar la información para **poblar una base de datos propia en Supabase**. Esto nos permitirá eliminar la dependencia de APIs de terceros limitadas, tener el control total sobre un *Single Source of Truth* del ecosistema Star Wars, y exponer esos datos limpios a otras aplicaciones de forma confiable.
*   **Observabilidad y Trazabilidad:** Integración de OpenTelemetry para trackear con mayor granularidad el tiempo específico que toman las requests de HTTP frente al procesamiento local.
*   **Pipeline de Integración Continua (CI):** Adoptar workflows de GitHub Actions para disparar linters (`ruff`), comprobadores de tipado (`mypy`) y los Unit Tests ante nuevos PRs y proteger ramas main.
