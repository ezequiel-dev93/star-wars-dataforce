from __future__ import annotations
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class PhysicalTraits(BaseModel):
    height_cm: Optional[float] = Field(None, ge=0)
    mass_kg: Optional[float] = Field(None, ge=0)
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None

    @field_validator('hair_color', 'eye_color', mode='before')
    @classmethod
    def normalize_unknown(cls, v: object) -> Optional[str]:
        if isinstance(v, str) and v.strip().lower() in {'unknown', 'n/a', 'none', ''}:
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
    homeworld: Optional[str] = None
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('slug', mode='before')
    @classmethod
    def build_slug(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError('El slug debe ser str')
        s = v.strip().lower()
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_]+', '-', s)
        s = re.sub(r'-{2,}', '-', s)
        return s.strip('-')

    @field_validator('gender', mode='before')
    @classmethod
    def normalize_gender(cls, v: object) -> Optional[str]:
        if isinstance(v, str) and v.strip().lower() in {'unknown', 'n/a', 'none', ''}:
            return None
        return v

    @field_validator('species', 'affiliations', 'masters', 'apprentices', 'appearances', 'portrayed_by', mode='before')
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
