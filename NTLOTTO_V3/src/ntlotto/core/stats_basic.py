from __future__ import annotations
import pandas as pd
from .util_format import band_of, BANDS

def sum6(df_s: pd.DataFrame) -> pd.Series:
    return df_s[[f"n{i}" for i in range(1,7)]].sum(axis=1)

def odd_even_profile(df_s: pd.DataFrame) -> dict[str,int]:
    out: dict[str,int] = {}
    for _, r in df_s.iterrows():
        nums = [int(r[f"n{i}"]) for i in range(1,7)]
        odd = sum(1 for x in nums if x % 2 == 1)
        even = 6 - odd
        k = f"{odd}:{even}"
        out[k] = out.get(k, 0) + 1
    return out

def bands_profile(df_s: pd.DataFrame) -> dict[str,float]:
    counts = {b: 0 for b in BANDS}
    for _, r in df_s.iterrows():
        nums = [int(r[f"n{i}"]) for i in range(1,7)]
        for n in nums:
            counts[band_of(n)] += 1
    n_draws = max(1, len(df_s))
    return {b: counts[b]/n_draws for b in BANDS}

def max_run_len(nums_sorted: list[int]) -> int:
    best = 1
    cur = 1
    for i in range(1, len(nums_sorted)):
        if nums_sorted[i] == nums_sorted[i-1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best

def run_profile(df_s: pd.DataFrame) -> dict[str,int]:
    out = {"1":0,"2":0,"3+":0}
    for _, r in df_s.iterrows():
        nums = sorted([int(r[f"n{i}"]) for i in range(1,7)])
        m = max_run_len(nums)
        if m <= 1: out["1"] += 1
        elif m == 2: out["2"] += 1
        else: out["3+"] += 1
    return out

def same_end_groups(nums: list[int]) -> int:
    ends: dict[int,int] = {}
    for n in nums:
        d = n % 10
        ends[d] = ends.get(d, 0) + 1
    return sum(1 for _,c in ends.items() if c >= 2)

def end_group_profile(df_s: pd.DataFrame) -> dict[str,int]:
    out = {"0":0,"1":0,"2":0,"3+":0}
    for _, r in df_s.iterrows():
        nums = [int(r[f"n{i}"]) for i in range(1,7)]
        g = same_end_groups(nums)
        if g <= 0: out["0"] += 1
        elif g == 1: out["1"] += 1
        elif g == 2: out["2"] += 1
        else: out["3+"] += 1
    return out
