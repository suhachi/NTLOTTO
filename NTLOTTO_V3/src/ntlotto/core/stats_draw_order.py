from __future__ import annotations
from collections import Counter
import numpy as np
import pandas as pd

def gap_stats(df_o: pd.DataFrame) -> dict[str,float]:
    gaps=[]
    for _, r in df_o.iterrows():
        bs = [int(r[f"b{i}"]) for i in range(1,7)]
        for i in range(5):
            gaps.append(abs(bs[i+1]-bs[i]))
    if not gaps:
        return {"mean":0.0,"median":0.0}
    return {"mean": float(np.mean(gaps)), "median": float(np.median(gaps))}

def top_transitions(df_o: pd.DataFrame, k: int = 10) -> list[tuple[tuple[int,int], int]]:
    c=Counter()
    for _, r in df_o.iterrows():
        bs = [int(r[f"b{i}"]) for i in range(1,7)]
        for i in range(5):
            c[(bs[i], bs[i+1])] += 1
    return sorted(c.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))[:k]
