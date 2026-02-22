from __future__ import annotations
import pandas as pd

def recency_prev1(df_s: pd.DataFrame) -> list[int]:
    vals=[]
    rows = df_s.sort_values("round").reset_index(drop=True)
    for i in range(1, len(rows)):
        cur = set(int(rows.loc[i, f"n{j}"]) for j in range(1,7))
        prev = set(int(rows.loc[i-1, f"n{j}"]) for j in range(1,7))
        vals.append(len(cur & prev))
    return vals

def recency_overlaps(df_s: pd.DataFrame, k: int) -> list[int]:
    vals=[]
    rows = df_s.sort_values("round").reset_index(drop=True)
    for i in range(1, len(rows)):
        cur = set(int(rows.loc[i, f"n{j}"]) for j in range(1,7))
        start = max(0, i-k)
        prev_union=set()
        for t in range(start, i):
            prev_union |= set(int(rows.loc[t, f"n{j}"]) for j in range(1,7))
        vals.append(len(cur & prev_union))
    return vals
