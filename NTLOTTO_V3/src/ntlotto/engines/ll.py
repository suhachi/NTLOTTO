"""
[NT-LL 엔진 정의]
- 역할: 최근 흐름 변화(드리프트)에 반응하는 보정축
- 입력: ssot_sorted
- 출력: score_map, candidate_pool
- 주의: 노이즈에도 반응 가능 → 단독 주력 금지(보조 슬롯)
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase

class EngineLL(EngineBase):
    def __init__(self):
        super().__init__("LL")
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        # drift 기반 스터브
        return {i: 0.5 for i in range(1, 46)}
