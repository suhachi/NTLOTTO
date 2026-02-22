"""
[NT-Ω 엔진 정의]
- 역할: 최근성(5~10 재사용) + 분산/커버리지 경고 축
- 입력: ssot_sorted
- 출력: score_map, candidate_pool(K_pool 기본 22~30)
- 주의: 메타(NTO)와 TopK가 과도하게 같아지면 의미 감소 → 독립성 점검 항목 포함
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase

class EngineOmega(EngineBase):
    def __init__(self):
        super().__init__("Omega")
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        counts = {i: 0.1 for i in range(1, 46)}
        if len(df_s) > 0:
            # 이월 후보군 점수 높임
            for j in range(1,7):
                counts[int(df_s.iloc[-1][f"n{j}"])] += 1.0
            mx = max(counts.values())
            return {k: v/mx for k,v in counts.items()}
        return counts
