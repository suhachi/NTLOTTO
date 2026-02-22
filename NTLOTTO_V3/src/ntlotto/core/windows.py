from __future__ import annotations
import pandas as pd

def last_n(df: pd.DataFrame, n: int) -> pd.DataFrame:
    df = df.sort_values("round")
    if len(df) <= n:
        return df.copy()
    return df.tail(n).copy()

def window_map(df: pd.DataFrame, ns: list[int]) -> dict[int, pd.DataFrame]:
    return {n: last_n(df, n) for n in ns}
