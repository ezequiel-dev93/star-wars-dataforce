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
