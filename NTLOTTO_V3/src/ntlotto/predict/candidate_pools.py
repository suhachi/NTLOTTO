from __future__ import annotations
import pandas as pd
from ..engines.base import EngineBase

def build_candidate_pools(
    engines: dict[str, EngineBase],
    df_s: pd.DataFrame,
    df_o: pd.DataFrame,
    pool_size: int = 15
) -> dict[str, list[int]]:
    """
    각 엔진별로 점수를 계산하여 상위 pool_size 개의 번호 목록을
    독립적으로 생성하여 반환함.
    """
    pools = {}
    for name, eng in engines.items():
        score_map = eng.score_map(df_s, df_o)
        sorted_nums = sorted(score_map.items(), key=lambda x: -x[1])
        top_nums = [n for n, s in sorted_nums[:pool_size]]
        pools[name] = sorted(top_nums)
        
    return pools
