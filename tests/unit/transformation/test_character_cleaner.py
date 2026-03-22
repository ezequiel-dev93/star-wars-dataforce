import pandas as pd
import pytest
from src.transformation.cleaners.character_cleaner import CharacterCleaner, _to_float, _to_slug, _extract_id

RAW = [
    {
        'name': 'Luke Skywalker', 'height': '172', 'mass': '77',
        'hair_color': 'blond', 'eye_color': 'blue', 'gender': 'male',
        'homeworld': 'https://swapi.dev/api/planets/1/',
        'films': ['https://swapi.dev/api/films/1/', 'https://swapi.dev/api/films/2/'],
        'url': 'https://swapi.dev/api/people/1/',
    },
    {
        'name': 'C-3PO', 'height': '167', 'mass': '75',
        'hair_color': 'n/a', 'eye_color': 'yellow', 'gender': 'n/a',
        'homeworld': 'https://swapi.dev/api/planets/1/',
        'films': [], 'url': 'https://swapi.dev/api/people/2/',
    },
]

FILM_MAP = {
    'https://swapi.dev/api/films/1/': 'A New Hope',
    'https://swapi.dev/api/films/2/': 'The Empire Strikes Back',
}

PLANET_MAP = {
    'https://swapi.dev/api/planets/1/': 'Tatooine',
}

def test_to_float_numeric():
    assert _to_float('172') == 172.0

def test_to_float_unknown():
    assert _to_float('unknown') is None

def test_to_slug_simple():
    assert _to_slug('Luke Skywalker') == 'luke-skywalker'

def test_to_slug_special():
    assert _to_slug('C-3PO!') == 'c-3po'

def test_extract_id():
    assert _extract_id('https://swapi.dev/api/people/1/') == 1

def test_clean_correct_columns():
    df = CharacterCleaner().clean(RAW)
    assert {'id', 'slug', 'name', 'height_cm', 'mass_kg'}.issubset(set(df.columns))

def test_clean_ids():
    df = CharacterCleaner().clean(RAW)
    assert list(df['id']) == [1, 2]

def test_clean_height_to_float():
    df = CharacterCleaner().clean(RAW)
    assert df.loc[df['name'] == 'Luke Skywalker', 'height_cm'].values[0] == 172.0

def test_clean_unknown_hair_none():
    df = CharacterCleaner().clean(RAW)
    assert pd.isna(df.loc[df['name'] == 'C-3PO', 'hair_color'].values[0])

def test_clean_empty_returns_empty_df():
    assert CharacterCleaner().clean([]).empty

def test_appearances_with_film_map_returns_titles():
    df = CharacterCleaner().clean(RAW, film_map=FILM_MAP)
    appearances = df.loc[df['name'] == 'Luke Skywalker', 'appearances'].values[0]
    assert appearances == ['A New Hope', 'The Empire Strikes Back']

def test_appearances_without_film_map_returns_urls():
    df = CharacterCleaner().clean(RAW)
    appearances = df.loc[df['name'] == 'Luke Skywalker', 'appearances'].values[0]
    assert all('swapi.dev' in url for url in appearances)

def test_appearances_empty_list():
    df = CharacterCleaner().clean(RAW, film_map=FILM_MAP)
    appearances = df.loc[df['name'] == 'C-3PO', 'appearances'].values[0]
    assert appearances == []

def test_homeworld_resolved_with_planet_map():
    df = CharacterCleaner().clean(RAW, planet_map=PLANET_MAP)
    hw = df.loc[df['name'] == 'Luke Skywalker', 'homeworld'].values[0]
    assert hw == 'Tatooine'

def test_homeworld_without_planet_map_keeps_url():
    df = CharacterCleaner().clean(RAW)
    hw = df.loc[df['name'] == 'Luke Skywalker', 'homeworld'].values[0]
    assert 'swapi.dev' in hw
