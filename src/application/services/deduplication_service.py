"""
Servicio de deduplicación y fusión (merge) inteligente de personajes.

Permite consolidar personajes extraídos de múltiples fuentes (SWAPI, películas,
series de Databank) sin perder información (fusiona apariciones, afiliaciones,
fotos y elige las descripciones más ricas).
"""
from __future__ import annotations
from typing import Sequence
from src.core.entities.character import CharacterEntity, normalize_slug


def _merge_unique_lists(list_a: list[str] | None, list_b: list[str] | None) -> list[str]:
    """Combina dos listas de strings preservando orden y eliminando duplicados (case-insensitive)."""
    seen: set[str] = set()
    result: list[str] = []
    
    for item in (list_a or []) + (list_b or []):
        if not item or not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
            
    return result


def _is_better_description(new_desc: str | None, current_desc: str | None) -> bool:
    """Evalúa si una descripción nueva es cualitativamente mejor que la actual."""
    if not new_desc:
        return False
    clean_new = new_desc.strip()
    if not clean_new or clean_new.startswith("No description available for"):
        return False
        
    if not current_desc or current_desc.startswith("No description available for"):
        return True
        
    # Preferir la descripción más detallada / con mayor cantidad de palabras
    words_new = len(clean_new.split())
    words_curr = len(current_desc.strip().split())
    return words_new > words_curr


def deduplicate_and_merge_characters(
    characters: Sequence[CharacterEntity],
) -> list[CharacterEntity]:
    """
    Fusiona y deduplica una colección de personajes por su slug único.

    Reglas de fusión:
    1. 'appearances', 'affiliations', 'species', 'planets', 'masters', 'apprentices', 'portrayed_by':
       Se combinan todas las listas sin duplicados.
    2. 'description': Se mantiene la descripción más extensa y de mayor calidad.
    3. 'avatar_url': Si el personaje no tenía imagen y el duplicado sí, se incorpora.
    4. 'physical_traits': Si falta algún rasgo (altura, ojos, pelo) y el duplicado lo tiene, se completa.
    5. 'gender', 'birth', 'death': Se enriquecen si estaban vacíos.
    6. 'id': Se re-secuencian desde 1.
    """
    merged: dict[str, CharacterEntity] = {}

    for char in characters:
        slug = normalize_slug(char.slug or char.name)

        if slug not in merged:
            # Clonar o asignar directamente
            merged[slug] = char.model_copy(deep=True)
            continue

        target = merged[slug]

        # 1. Fusionar listas de texto
        target.appearances = _merge_unique_lists(target.appearances, char.appearances)
        target.affiliations = _merge_unique_lists(target.affiliations, char.affiliations)
        target.species = _merge_unique_lists(target.species, char.species)
        target.planets = _merge_unique_lists(target.planets, char.planets)
        target.masters = _merge_unique_lists(target.masters, char.masters)
        target.apprentices = _merge_unique_lists(target.apprentices, char.apprentices)
        target.portrayed_by = _merge_unique_lists(target.portrayed_by, char.portrayed_by)

        # 2. Descripción más rica
        if _is_better_description(char.description, target.description):
            target.description = char.description.strip()

        # 3. Avatar / Imagen
        if not target.avatar_url and char.avatar_url:
            target.avatar_url = char.avatar_url

        # 4. Rasgos físicos
        if target.physical_traits.height_cm is None and char.physical_traits.height_cm is not None:
            target.physical_traits.height_cm = char.physical_traits.height_cm
        if target.physical_traits.mass_kg is None and char.physical_traits.mass_kg is not None:
            target.physical_traits.mass_kg = char.physical_traits.mass_kg
        if not target.physical_traits.hair_color and char.physical_traits.hair_color:
            target.physical_traits.hair_color = char.physical_traits.hair_color
        if not target.physical_traits.eye_color and char.physical_traits.eye_color:
            target.physical_traits.eye_color = char.physical_traits.eye_color

        # 5. Género
        if not target.gender and char.gender:
            target.gender = char.gender

        # 6. Nacimiento / Muerte
        if not target.birth.year and char.birth.year:
            target.birth.year = char.birth.year
        if not target.birth.location and char.birth.location:
            target.birth.location = char.birth.location
        if not target.death.year and char.death.year:
            target.death.year = char.death.year
        if not target.death.location and char.death.location:
            target.death.location = char.death.location

        # 7. Force sensitive & Canon
        target.force_sensitive = target.force_sensitive or char.force_sensitive
        target.is_canon = target.is_canon and char.is_canon

    # Reindexar IDs secuenciales
    result_list = list(merged.values())
    for idx, entity in enumerate(result_list, start=1):
        entity.id = idx

    return result_list
