from __future__ import annotations
from collections import Counter
import pandas as pd

def freq_counts(df_s: pd.DataFrame) -> Counter:
    c=Counter()
    for _, r in df_s.iterrows():
        c.update([int(r[f"n{i}"]) for i in range(1,7)])
    return c

def topk_freq(df_s: pd.DataFrame, k: int = 10) -> list[tuple[int,int]]:
    c = freq_counts(df_s)
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))[:k]

def bottomk_freq(df_s: pd.DataFrame, k: int = 10) -> list[tuple[int,int]]:
    c = freq_counts(df_s)
    return sorted(c.items(), key=lambda x: (x[1], x[0]))[:k]
