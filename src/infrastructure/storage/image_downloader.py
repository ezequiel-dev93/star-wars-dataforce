"""
Descargador asíncrono y robusto de imágenes.

Características:
- Omite descargas si el archivo ya existe localmente.
- Optimiza URLs de CDN (Disney/Lumiere) para obtener máxima resolución.
- Control de concurrencia mediante Semaphore.
- Reintentos con retroceso exponencial.
- Verificación de Content-Type de imagen.
"""
from __future__ import annotations
import asyncio
import re
from pathlib import Path
import httpx
from src.config.logging.logger import get_logger

logger = get_logger(__name__)


ANIMATION_KEYWORDS = (
    "tcw",
    "the clone wars",
    "clone wars",
    "clone-wars",
    "clonewars",
    "rebels",
    "bad batch",
    "bad-batch",
    "badbatch",
    "resistance",
    "visions",
    "tales of the jedi",
    "tales-of-the-jedi",
    "tales of the empire",
    "tales-of-the-empire",
    "young jedi",
    "young-jedi",
    "animation",
    "animated",
    "cartoon",
    "forces-of-destiny",
    "forces of destiny",
    "droids",
    "ewoks-animated",
)


def is_animated_image(url: str, alt_text: str = "") -> bool:
    """Detecta si una URL o etiqueta alt corresponde a contenido animado o dibujo."""
    combined = f"{url.lower()} {alt_text.lower()}"
    normalized = re.sub(r'[-_]+', ' ', combined)
    return any(k in combined or k in normalized for k in ANIMATION_KEYWORDS)


def clean_image_url(url: str) -> str:
    """
    Limpia parámetros de compresión o recorte pequeño en URLs de Akamai/Disney.
    Ej: remueve '&width=320' para obtener la versión de mayor resolución.
    """
    if not url:
        return ""
    # Quitar width reducido
    cleaned = re.sub(r'([?&])width=\d+', '', url)
    # Limpiar restos de sintaxis de query string
    cleaned = re.sub(r'\?&', '?', cleaned)
    cleaned = re.sub(r'[\?&]$', '', cleaned)
    return cleaned


class ImageDownloader:
    """
    Maneja la descarga y almacenamiento local de imágenes de personajes.
    """

    def __init__(
        self,
        output_dir: Path | str = Path("output/images/characters"),
        concurrency: int = 5,
        timeout: float = 15.0,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._semaphore = asyncio.Semaphore(concurrency)
        self._timeout = timeout

    def get_existing_image(self, slug: str) -> Path | None:
        """Verifica si ya existe una imagen para este slug en cualquiera de sus extensiones válidas."""
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            candidate = self.output_dir / f"{slug}{ext}"
            if candidate.is_file() and candidate.stat().st_size > 500:  # Archivo no vacío
                return candidate
        return None

    async def download_character_image(
        self,
        slug: str,
        image_url: str,
        client: httpx.AsyncClient | None = None,
        retries: int = 3,
        allow_animated: bool = False,
    ) -> Path | None:
        """
        Descarga la imagen del personaje si no existe localmente.

        Args:
            slug: Identificador único del personaje.
            image_url: URL de la imagen.
            client: Cliente HTTP opcional (para reusar conexiones).
            retries: Número de reintentos en caso de fallo de red.
            allow_animated: Si es True, permite descargar ilustraciones oficiales
                           para personajes nacidos exclusivamente en series animadas.

        Returns:
            Path al archivo local guardado o None si falló/no tenía URL.
        """
        if not image_url or not image_url.startswith("http"):
            return None

        # 1. Comprobar si ya existe localmente
        existing = self.get_existing_image(slug)
        if existing:
            logger.debug(f"[CACHE] Imagen ya existe para '{slug}': {existing.name}")
            return existing

        # 2. Descartar si es una imagen animada/dibujo y no está expresamente permitida
        if not allow_animated and is_animated_image(image_url):
            logger.warning(f"[SKIP DIBUJO/ANIMACIÓN] Imagen descartada para '{slug}': {image_url}")
            return None

        cleaned_url = clean_image_url(image_url)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }

        async with self._semaphore:
            should_close_client = False
            if client is None:
                client = httpx.AsyncClient(timeout=self._timeout, follow_redirects=True)
                should_close_client = True

            try:
                for attempt in range(1, retries + 1):
                    try:
                        response = await client.get(cleaned_url, headers=headers)
                        if response.status_code == 200:
                            content_type = response.headers.get("content-type", "").lower()
                            # Determinar extensión
                            ext = ".jpg"
                            if "png" in content_type:
                                ext = ".png"
                            elif "webp" in content_type:
                                ext = ".webp"
                            elif "jpeg" in content_type:
                                ext = ".jpeg"

                            dest_file = self.output_dir / f"{slug}{ext}"
                            dest_file.write_bytes(response.content)
                            logger.info(f"[IMAGE OK] Descargada imagen para '{slug}' -> {dest_file.name}")
                            return dest_file
                        elif response.status_code == 404:
                            logger.warning(f"[IMAGE 404] Imagen no encontrada para '{slug}': {cleaned_url}")
                            return None
                        else:
                            logger.warning(
                                f"[IMAGE RETRY {attempt}/{retries}] Status {response.status_code} para '{slug}'"
                            )
                    except (httpx.RequestError, httpx.TimeoutException) as exc:
                        logger.warning(f"[IMAGE RETRY {attempt}/{retries}] Error descargando '{slug}': {exc}")
                        if attempt == retries:
                            return None
                        await asyncio.sleep(1.0 * attempt)
            finally:
                if should_close_client:
                    await client.aclose()

        return None
