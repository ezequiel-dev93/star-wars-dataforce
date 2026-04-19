import pytest
from src.core.entities.character import CharacterEntity, PhysicalTraits

def mk(**overrides):
    base = dict(id=1, slug='luke-skywalker', name='Luke Skywalker')
    base.update(overrides)
    return base

def test_valid_character():
    c = CharacterEntity(**mk())
    assert c.id == 1 and c.slug == 'luke-skywalker' and c.is_canon is True

def test_slug_normalized():
    c = CharacterEntity(**mk(slug='Darth Vader!'))
    assert c.slug == 'darth-vader'

def test_description_fallback():
    c = CharacterEntity(**mk(description=''))
    assert 'Luke Skywalker' in c.description

def test_physical_traits_unknown_to_none():
    t = PhysicalTraits(hair_color='unknown', eye_color='n/a')
    assert t.hair_color is None and t.eye_color is None

def test_invalid_id_raises():
    with pytest.raises(Exception):
        CharacterEntity(**mk(id=0))

def test_ensure_list_from_string():
    c = CharacterEntity(**mk(species='Human'))
    assert c.species == ['Human']

def test_ensure_list_from_none():
    c = CharacterEntity(**mk(affiliations=None))
    assert c.affiliations == []

def test_gender_unknown_to_none():
    c = CharacterEntity(**mk(gender='unknown'))
    assert c.gender is None


# ── PhysicalTraits: coercion numerica (antes duplicada en mapper) ────────

def test_height_string_to_float():
    t = PhysicalTraits(height_cm='172')
    assert t.height_cm == 172.0

def test_mass_string_to_float():
    t = PhysicalTraits(mass_kg='77')
    assert t.mass_kg == 77.0

def test_height_unknown_to_none():
    t = PhysicalTraits(height_cm='unknown')
    assert t.height_cm is None

def test_mass_na_to_none():
    t = PhysicalTraits(mass_kg='n/a')
    assert t.mass_kg is None

def test_height_comma_decimal():
    t = PhysicalTraits(height_cm='1,72')
    assert t.height_cm == 1.72

def test_height_none_stays_none():
    t = PhysicalTraits(height_cm=None)
    assert t.height_cm is None

def test_height_float_stays_float():
    t = PhysicalTraits(height_cm=180.5)
    assert t.height_cm == 180.5
