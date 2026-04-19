from __future__ import annotations
import re
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

_UNKNOWN_VALUES = {'unknown', 'n/a', 'none', '', 'na'}


def normalize_slug(value: str) -> str:
    """Normaliza un string a slug consistente con CharacterEntity.

    Convierte a minúsculas, remueve caracteres especiales,
    reemplaza espacios con guiones, y elimina guiones duplicados.
    """
    s = value.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-{2,}', '-', s)
    return s.strip('-')


class PhysicalTraits(BaseModel):
    height_cm: Optional[float] = Field(None, ge=0)
    mass_kg: Optional[float] = Field(None, ge=0)
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None

    @field_validator('height_cm', 'mass_kg', mode='before')
    @classmethod
    def coerce_numeric(cls, v: object) -> Optional[float]:
        """Convierte strings numericos a float y valores desconocidos a None."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace(',', '.').strip()
            if cleaned.lower() in _UNKNOWN_VALUES:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @field_validator('hair_color', 'eye_color', mode='before')
    @classmethod
    def normalize_unknown(cls, v: object) -> Optional[str]:
        if isinstance(v, str) and v.strip().lower() in _UNKNOWN_VALUES:
            return None
        return v

class BirthInfo(BaseModel):
    year: Optional[str] = None
    location: Optional[str] = None

class DeathInfo(BaseModel):
    year: Optional[str] = None
    location: Optional[str] = None

class CharacterEntity(BaseModel):
    model_config = {'str_strip_whitespace': True, 'validate_assignment': True}

    id: int = Field(..., gt=0)
    slug: str
    name: str = Field(..., min_length=1)
    physical_traits: PhysicalTraits = Field(default_factory=PhysicalTraits)
    gender: Optional[str] = None
    species: list[str] = Field(default_factory=list)
    planets: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    masters: list[str] = Field(default_factory=list)
    apprentices: list[str] = Field(default_factory=list)
    description: str = ''
    appearances: list[str] = Field(default_factory=list)
    portrayed_by: list[str] = Field(default_factory=list)
    birth: BirthInfo = Field(default_factory=BirthInfo)
    death: DeathInfo = Field(default_factory=DeathInfo)
    force_sensitive: bool = False
    is_canon: bool = True
    avatar_url: str = ''
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator('slug', mode='before')
    @classmethod
    def build_slug(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError('El slug debe ser str')
        return normalize_slug(v)

    @field_validator('gender', mode='before')
    @classmethod
    def normalize_gender(cls, v: object) -> Optional[str]:
        if isinstance(v, str) and v.strip().lower() in _UNKNOWN_VALUES:
            return None
        return v

    @field_validator('species', 'planets', 'affiliations', 'masters', 'apprentices', 'appearances', 'portrayed_by', mode='before')
    @classmethod
    def ensure_list(cls, v: object) -> list:
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        return list(v)

    @model_validator(mode='after')
    def description_fallback(self) -> 'CharacterEntity':
        if not self.description:
            self.description = f'No description available for {self.name}.'
        return self
