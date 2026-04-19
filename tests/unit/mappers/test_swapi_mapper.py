import pytest
from src.application.mappers.swapi_mapper import (
    SwapiMapper, _extract_id, _resolve_url_list,
)

RAW = [
    {
        'name': 'Luke Skywalker', 'height': '172', 'mass': '77',
        'hair_color': 'blond', 'eye_color': 'blue', 'gender': 'male',
        'homeworld': 'https://swapi.dev/api/planets/1/',
        'films': ['https://swapi.dev/api/films/1/', 'https://swapi.dev/api/films/2/'],
        'species': [],
        'birth_year': '19BBY',
        'url': 'https://swapi.dev/api/people/1/',
    },
    {
        'name': 'C-3PO', 'height': '167', 'mass': '75',
        'hair_color': 'n/a', 'eye_color': 'yellow', 'gender': 'n/a',
        'homeworld': 'https://swapi.dev/api/planets/1/',
        'films': [],
        'species': ['https://swapi.dev/api/species/2/'],
        'birth_year': '112BBY',
        'url': 'https://swapi.dev/api/people/2/',
    },
]

FILM_MAP = {
    'https://swapi.dev/api/films/1/': 'A New Hope',
    'https://swapi.dev/api/films/2/': 'The Empire Strikes Back',
}

PLANET_MAP = {
    'https://swapi.dev/api/planets/1/': 'Tatooine',
}

SPECIES_MAP = {
    'https://swapi.dev/api/species/2/': 'Droid',
}


# ── Utilidades ────────────────────────────────────────────────────────────

def test_extract_id():
    assert _extract_id('https://swapi.dev/api/people/1/') == 1

def test_extract_id_returns_none_on_bad_url():
    assert _extract_id('no-url') is None

def test_resolve_url_list_with_map():
    urls = ['https://swapi.dev/api/films/1/']
    assert _resolve_url_list(urls, FILM_MAP) == ['A New Hope']

def test_resolve_url_list_missing_key():
    urls = ['https://swapi.dev/api/films/99/']
    result = _resolve_url_list(urls, FILM_MAP)
    assert result == ['https://swapi.dev/api/films/99/']

def test_resolve_url_list_not_a_list():
    assert _resolve_url_list(None, FILM_MAP) == []


# ── SwapiMapper ─────────────────────────────────────────────────────

def _find(results: list[dict], name: str) -> dict:
    """Helper para encontrar un personaje por nombre en los resultados."""
    return next(r for r in results if r['name'] == name)


def test_map_empty_returns_empty():
    assert SwapiMapper().map_to_dicts([]) == []

def test_map_returns_correct_ids():
    results = SwapiMapper().map_to_dicts(RAW)
    assert [r['id'] for r in results] == [1, 2]

def test_map_passes_raw_height_for_pydantic():
    """El mapper ya NO parsea floats; le pasa el string crudo a Pydantic."""
    results = SwapiMapper().map_to_dicts(RAW)
    luke = _find(results, 'Luke Skywalker')
    assert luke['physical_traits']['height_cm'] == '172'

def test_map_passes_raw_hair_for_pydantic():
    """El mapper ya NO limpia 'n/a'; Pydantic lo hace."""
    results = SwapiMapper().map_to_dicts(RAW)
    c3po = _find(results, 'C-3PO')
    assert c3po['physical_traits']['hair_color'] == 'n/a'

def test_map_skips_entries_without_url():
    bad_data = [{'name': 'Ghost', 'height': '100'}]
    assert SwapiMapper().map_to_dicts(bad_data) == []


# ── Appearances ──────────────────────────────────────────────────────────

def test_appearances_with_film_map_returns_titles():
    results = SwapiMapper().map_to_dicts(RAW, film_map=FILM_MAP)
    luke = _find(results, 'Luke Skywalker')
    assert luke['appearances'] == ['A New Hope', 'The Empire Strikes Back']

def test_appearances_without_film_map_returns_urls():
    results = SwapiMapper().map_to_dicts(RAW)
    luke = _find(results, 'Luke Skywalker')
    assert all('swapi.dev' in url for url in luke['appearances'])

def test_appearances_empty_list():
    results = SwapiMapper().map_to_dicts(RAW, film_map=FILM_MAP)
    c3po = _find(results, 'C-3PO')
    assert c3po['appearances'] == []


# ── Planets ───────────────────────────────────────────────────────────────

def test_planets_resolved_with_planet_map():
    results = SwapiMapper().map_to_dicts(RAW, planet_map=PLANET_MAP)
    luke = _find(results, 'Luke Skywalker')
    assert luke['planets'] == 'Tatooine'

def test_planets_without_planet_map_keeps_url():
    results = SwapiMapper().map_to_dicts(RAW)
    luke = _find(results, 'Luke Skywalker')
    assert 'swapi.dev' in luke['planets']


# ── Species ──────────────────────────────────────────────────────────────

def test_species_resolved_with_species_map():
    results = SwapiMapper().map_to_dicts(RAW, species_map=SPECIES_MAP)
    c3po = _find(results, 'C-3PO')
    assert c3po['species'] == ['Droid']

def test_species_empty_stays_empty():
    results = SwapiMapper().map_to_dicts(RAW, species_map=SPECIES_MAP)
    luke = _find(results, 'Luke Skywalker')
    assert luke['species'] == []

def test_species_without_map_keeps_urls():
    results = SwapiMapper().map_to_dicts(RAW)
    c3po = _find(results, 'C-3PO')
    assert all('swapi.dev' in url for url in c3po['species'])


# ── Birth year ───────────────────────────────────────────────────────────

def test_birth_year_passed_through():
    results = SwapiMapper().map_to_dicts(RAW)
    luke = _find(results, 'Luke Skywalker')
    assert luke['birth']['year'] == '19BBY'

def test_birth_year_c3po():
    results = SwapiMapper().map_to_dicts(RAW)
    c3po = _find(results, 'C-3PO')
    assert c3po['birth']['year'] == '112BBY'
