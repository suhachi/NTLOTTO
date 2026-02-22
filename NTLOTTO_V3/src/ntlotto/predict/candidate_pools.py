from __future__ import annotations
import pandas as pd
from ..engines.base import EngineBase

def build_candidate_pools(
    engines: dict[str, EngineBase],
    df_s: pd.DataFrame,
    df_o: pd.DataFrame,
) -> dict[str, dict[int, float]]:
    """
    각 엔진별로 score_map 객체를 반환하여, 
    후보풀 생성 단계에서 가중치 샘플링을 할 수 있도록 함.
    """
    pools = {}
    for name, eng in engines.items():
        pools[name] = eng.score_map(df_s, df_o)
        
    return pools
