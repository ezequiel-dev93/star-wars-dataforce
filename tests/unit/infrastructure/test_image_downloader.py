from pathlib import Path
import pytest
from src.infrastructure.storage.image_downloader import clean_image_url, ImageDownloader


def test_clean_image_url():
    raw_url = "https://lumiere-a.akamaihd.net/v1/images/mando.jpeg?region=0,0,100,100&width=320"
    cleaned = clean_image_url(raw_url)
    assert "&width=320" not in cleaned
    assert "region=0,0,100,100" in cleaned


def test_get_existing_image_finds_file(tmp_path: Path):
    downloader = ImageDownloader(output_dir=tmp_path)
    sample_file = tmp_path / "grogu.jpg"
    sample_file.write_bytes(b"dummy image data" * 100)

    found = downloader.get_existing_image("grogu")
    assert found is not None
    assert found.name == "grogu.jpg"

    not_found = downloader.get_existing_image("non-existent")
    assert not_found is None


def test_is_animated_image_detection():
    from src.infrastructure.storage.image_downloader import is_animated_image

    assert is_animated_image("https://lumiere-a.akamaihd.net/v1/images/ahsoka_tcw_hero.jpg") is True
    assert is_animated_image("https://lumiere-a.akamaihd.net/v1/images/bad-batch-main.jpg") is True
    assert is_animated_image("https://lumiere-a.akamaihd.net/v1/images/ahsoka-main.jpg", "The Clone Wars Ahsoka") is True
    assert is_animated_image("https://lumiere-a.akamaihd.net/v1/images/mando-main.jpg", "The Mandalorian Din Djarin") is False
    assert is_animated_image("https://lumiere-a.akamaihd.net/v1/images/ahsoka-main_88c206d7.jpeg") is False
