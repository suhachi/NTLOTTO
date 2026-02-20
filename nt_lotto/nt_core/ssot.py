import pandas as pd
import os
from typing import Set, Tuple, Optional
from .constants import SSOT_SORTED, SSOT_ORDERED, EXCLUDE_CSV

def load_exclude_rounds() -> Set[int]:
    """
    Load validation/exclusion rounds from CSV.
    Returns:
        Set[int]: Set of round numbers to exclude.
    """
    excludes = set()
    if os.path.exists(EXCLUDE_CSV):
        try:
            # Handle comments starting with '#'
            df = pd.read_csv(EXCLUDE_CSV, comment='#')
            if 'round' in df.columns:
                excludes = set(df['round'].unique().tolist())
        except Exception as e:
            print(f"[WARN] Failed to load exclusions: {e}")
    return excludes

def load_ssot_sorted() -> pd.DataFrame:
    """
    Load SSOT Sorted data (Label).
    Returns:
        pd.DataFrame: Columns [round, n1..n6, bonus]
    """
    if not os.path.exists(SSOT_SORTED):
        raise FileNotFoundError(f"SSOT Sorted not found: {SSOT_SORTED}")
    
    df = pd.read_csv(SSOT_SORTED)
    required_cols = ['round', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']
    
    # Validation
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"SSOT Sorted missing columns: {missing}")
        
    return df

def load_ssot_ordered() -> pd.DataFrame:
    """
    Load SSOT Ordered data (Feature - AL only).
    Returns:
        pd.DataFrame: Columns [round, b1..b6, bonus]
    """
    if not os.path.exists(SSOT_ORDERED):
        raise FileNotFoundError(f"SSOT Ordered not found: {SSOT_ORDERED}")
        
    df = pd.read_csv(SSOT_ORDERED)
    # Check common columns, usually b1..b6
    return df

def apply_exclusion(df: pd.DataFrame, exclude_set: Set[int]) -> pd.DataFrame:
    """
    Remove rows where 'round' is in exclude_set.
    """
    if 'round' not in df.columns:
        return df
    return df[~df['round'].isin(exclude_set)].copy()
