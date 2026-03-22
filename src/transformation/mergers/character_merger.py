from __future__ import annotations
import pandas as pd
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)

class CharacterMerger:
    def merge(self, swapi_df: pd.DataFrame, descriptions_df: pd.DataFrame) -> pd.DataFrame:
        if swapi_df.empty:
            return swapi_df
        if descriptions_df.empty:
            swapi_df['description'] = ''
            return swapi_df
        merged = swapi_df.merge(descriptions_df[['slug', 'description']], on='slug', how='left')
        merged['description'] = merged['description'].fillna('')
        matched = merged['description'].str.len().gt(0).sum()
        logger.info(f'[bold green]Merge:[/] {matched}/{len(merged)} con descripcion.')
        return merged
