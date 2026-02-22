from __future__ import annotations
import pandas as pd

def _check_range(vals: list[int], ctx: str) -> None:
    for v in vals:
        if not (1 <= int(v) <= 45):
            raise ValueError(f"{ctx}: 번호 범위(1..45) 위반: {v}")

def validate_ssot(df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict:
    if df_s["round"].duplicated().any():
        raise ValueError("sorted: round 중복")
    if df_o["round"].duplicated().any():
        raise ValueError("ordered: round 중복")

    set_s = set(df_s["round"].tolist())
    set_o = set(df_o["round"].tolist())
    if set_s != set_o:
        raise ValueError(f"round 집합 불일치: sorted-only={sorted(list(set_s-set_o))}, ordered-only={sorted(list(set_o-set_s))}")

    o_map = df_o.set_index("round")
    bad_sorted_order = 0

    for _, r in df_s.iterrows():
        R = int(r["round"])
        nums_s = [int(r[f"n{i}"]) for i in range(1,7)]
        b_s = int(r["bonus"])
        _check_range(nums_s+[b_s], f"sorted R{R}")

        if len(set(nums_s)) != 6:
            raise ValueError(f"sorted R{R}: 6개 중복")
        if b_s in nums_s:
            raise ValueError(f"sorted R{R}: bonus가 6개와 중복")

        if nums_s != sorted(nums_s):
            bad_sorted_order += 1

        o = o_map.loc[R]
        nums_o = [int(o[f"b{i}"]) for i in range(1,7)]
        b_o = int(o["bonus"])
        _check_range(nums_o+[b_o], f"ordered R{R}")

        if len(set(nums_o)) != 6:
            raise ValueError(f"ordered R{R}: 6개 중복")
        if b_o in nums_o:
            raise ValueError(f"ordered R{R}: bonus가 6개와 중복")

        if set(nums_s) != set(nums_o):
            raise ValueError(f"R{R}: sorted 6개 집합 != ordered 6개 집합")
        if b_s != b_o:
            raise ValueError(f"R{R}: bonus 불일치 sorted={b_s} ordered={b_o}")

    return {
        "rows": int(len(df_s)),
        "round_min": int(df_s["round"].min()),
        "round_max": int(df_s["round"].max()),
        "bad_sorted_order_rows": int(bad_sorted_order),
    }
