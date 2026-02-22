"""
[NT4 엔진 정의]
- 역할: 장기 빈도 + 최근 트렌드의 안정축
- 입력: ssot_sorted (주), ssot_ordered(미사용)
- 출력: score_map(1..45), candidate_pool(TopK; 기본 18~28)
- 금지: 최근성/핫클러스터 과도 편향 금지(단독 올인 비권장)
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase

class EngineNT4(EngineBase):
    def __init__(self):
        super().__init__("NT4")
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        # 장기 빈도
        counts = {i: 0.1 for i in range(1, 46)}
        n_rows = len(df_s)
        if n_rows > 0:
            for _, r in df_s.iterrows():
                for j in range(1,7):
                    counts[int(r[f"n{j}"])] += 1
            mx = max(counts.values())
            return {k: v/mx for k,v in counts.items()}
        return counts
