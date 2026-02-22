"""
[NT5 엔진 정의]
- 역할: 최근 5~10회 Hot 번호/클러스터 공격축
- 입력: ssot_sorted
- 출력: score_map, candidate_pool
- 금지: “완전 배제” 방식 금지(Cold=0 가정 금지), 가중치 차등만
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase

class EngineNT5(EngineBase):
    def __init__(self):
        super().__init__("NT5")
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        w10 = df_s.tail(10)
        counts = {i: 0.1 for i in range(1, 46)}
        if len(w10) > 0:
            for _, r in w10.iterrows():
                for j in range(1,7):
                    counts[int(r[f"n{j}"])] += 1
            mx = max(counts.values())
            return {k: v/mx for k,v in counts.items()}
        return counts
