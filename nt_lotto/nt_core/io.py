import pandas as pd
import os
from typing import Optional
from .schema import SSOT
from .constants import EXCLUDE_CSV

def load_ssot(draws_sorted_csv: str, draws_ordered_csv: str) -> SSOT:
    s = pd.read_csv(draws_sorted_csv)
    o = pd.read_csv(draws_ordered_csv)
    
    # Filter Exclusions
    if os.path.exists(EXCLUDE_CSV):
        exc_df = pd.read_csv(EXCLUDE_CSV)
        exc_rounds = set(exc_df["round"].tolist())
        s = s[~s["round"].isin(exc_rounds)].copy()
        o = o[~o["round"].isin(exc_rounds)].copy()
        
    _validate_sorted(s)
    _validate_ordered(o)
    _validate_alignment(s, o)
    return SSOT(sorted_df=s, ordered_df=o)

def _validate_sorted(df: pd.DataFrame) -> None:
    required = ["round","n1","n2","n3","n4","n5","n6","bonus"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"sorted_df missing column: {c}")

def _validate_ordered(df: pd.DataFrame) -> None:
    required = ["round","b1","b2","b3","b4","b5","b6","bonus"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"ordered_df missing column: {c}")

def _validate_alignment(sorted_df: pd.DataFrame, ordered_df: pd.DataFrame) -> None:
    sr = set(sorted_df["round"].tolist())
    orr = set(ordered_df["round"].tolist())
    if sr != orr:
        raise ValueError("round mismatch between sorted and ordered files")
