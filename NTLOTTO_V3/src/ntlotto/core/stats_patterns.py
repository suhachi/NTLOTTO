from __future__ import annotations
from collections import Counter
import pandas as pd

def top_pairs(df_s: pd.DataFrame, k: int = 15) -> list[tuple[tuple[int,int], int]]:
    c=Counter()
    for _, r in df_s.iterrows():
        nums = sorted([int(r[f"n{i}"]) for i in range(1,7)])
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                c[(nums[i], nums[j])] += 1
    return sorted(c.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))[:k]
