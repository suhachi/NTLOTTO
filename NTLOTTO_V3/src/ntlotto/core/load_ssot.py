from __future__ import annotations
import pandas as pd

SORTED_COLS = ["round","date","n1","n2","n3","n4","n5","n6","bonus"]
ORDERED_COLS = ["round","date","b1","b2","b3","b4","b5","b6","bonus"]

def load_ssot(sorted_path: str, ordered_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_s = pd.read_csv(sorted_path).dropna()
    df_o = pd.read_csv(ordered_path).dropna()

    if list(df_s.columns) != SORTED_COLS:
        raise ValueError(f"ssot_sorted.csv columns must be {SORTED_COLS}, got {list(df_s.columns)}")
    if list(df_o.columns) != ORDERED_COLS:
        raise ValueError(f"ssot_ordered.csv columns must be {ORDERED_COLS}, got {list(df_o.columns)}")

    df_s = df_s.copy()
    df_o = df_o.copy()

    df_s["round"] = df_s["round"].astype(int)
    df_o["round"] = df_o["round"].astype(int)

    for c in ["n1","n2","n3","n4","n5","n6","bonus"]:
        df_s[c] = df_s[c].astype(int)
    for c in ["b1","b2","b3","b4","b5","b6","bonus"]:
        df_o[c] = df_o[c].astype(int)

    df_s["date"] = df_s["date"].astype(str)
    df_o["date"] = df_o["date"].astype(str)

    return df_s, df_o
