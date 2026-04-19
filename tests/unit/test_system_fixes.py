"""Tests para verificar los fixes aplicados al sistema."""
import pytest
from datetime import datetime, UTC
from src.core.entities.character import (
    CharacterEntity, PhysicalTraits, BirthInfo, DeathInfo, normalize_slug
)


class TestNormalizeSlug:
    """Tests para la funcion utilitaria normalize_slug."""

    def test_normalize_slug_basic(self):
        assert normalize_slug('Luke Skywalker') == 'luke-skywalker'

    def test_normalize_slug_removes_special_chars(self):
        assert normalize_slug('Darth Vader!') == 'darth-vader'
        assert normalize_slug('C-3PO') == 'c-3po'
        assert normalize_slug('R2-D2!') == 'r2-d2'

    def test_normalize_slug_multiple_spaces(self):
        assert normalize_slug('Luke   Skywalker') == 'luke-skywalker'

    def test_normalize_slug_underscores(self):
        assert normalize_slug('Luke_Skywalker') == 'luke-skywalker'

    def test_normalize_slug_multiple_dashes(self):
        assert normalize_slug('Luke--Skywalker') == 'luke-skywalker'

    def test_normalize_slug_trailing_dashes(self):
        assert normalize_slug('-Luke Skywalker-') == 'luke-skywalker'

    def test_normalize_slug_empty_after_cleaning(self):
        assert normalize_slug('!!!') == ''


class TestCharacterEntitySlugValidation:
    """Tests para verificar que CharacterEntity usa normalize_slug correctamente."""

    def test_slug_via_pydantic_same_as_normalize_slug(self):
        """El slug generado por Pydantic debe ser igual al de normalize_slug."""
        test_cases = [
            'Darth Vader!',
            'Luke   Skywalker',
            'R2-D2!!!',
            '-Test User-',
            'Multiple___Underscores',
        ]
        for name in test_cases:
            entity = CharacterEntity.model_validate({
                'id': 1,
                'slug': name,
                'name': 'Test'
            })
            assert entity.slug == normalize_slug(name)


class TestDatetimeUTC:
    """Tests para verificar que se usa datetime.now(UTC) en lugar de utcnow()."""

    def test_created_at_uses_utc_timezone(self):
        """Verificar que created_at tiene timezone info (UTC)."""
        entity = CharacterEntity(id=1, slug='test', name='Test')
        assert entity.created_at.tzinfo == UTC

    def test_created_at_is_datetime(self):
        """Verificar que created_at es un objeto datetime."""
        entity = CharacterEntity(id=1, slug='test', name='Test')
        assert isinstance(entity.created_at, datetime)


class TestBirthDeathInfoDefaults:
    """Tests para verificar BirthInfo y DeathInfo funcionan correctamente."""

    def test_birth_info_empty(self):
        """BirthInfo puede crearse sin argumentos."""
        birth = BirthInfo()
        assert birth.year is None
        assert birth.location is None

    def test_death_info_empty(self):
        """DeathInfo puede crearse sin argumentos."""
        death = DeathInfo()
        assert death.year is None
        assert death.location is None

    def test_character_with_empty_birth_death(self):
        """CharacterEntity acepta BirthInfo() y DeathInfo() vacios."""
        entity = CharacterEntity(
            id=1,
            slug='test',
            name='Test',
            birth=BirthInfo(),
            death=DeathInfo()
        )
        assert entity.birth.year is None
        assert entity.death.year is None


class TestPhysicalTraitsEdgeCases:
    """Tests adicionales para PhysicalTraits."""

    def test_height_comma_decimal_spanish(self):
        """Altura con coma decimal (formato español)."""
        t = PhysicalTraits(height_cm='1,72')
        assert t.height_cm == 1.72

    def test_mass_with_whitespace(self):
        """Masa con espacios en blanco."""
        t = PhysicalTraits(mass_kg='  77  ')
        assert t.mass_kg == 77.0

    def test_height_invalid_string_returns_none(self):
        """Altura invalida retorna None."""
        t = PhysicalTraits(height_cm='tall')
        assert t.height_cm is None

    def test_hair_color_none_stays_none(self):
        """hair_color None se mantiene None."""
        t = PhysicalTraits(hair_color=None)
        assert t.hair_color is None

    def test_eye_color_empty_string_to_none(self):
        """eye_color string vacio se convierte a None."""
        t = PhysicalTraits(eye_color='')
        assert t.eye_color is None
