"""
[NT-VPA-1 엔진 정의]
- 역할: 번호대/연번/끝수 “모양(패턴)” 앵커 보조축
- 입력: ssot_sorted
- 출력: score_map(약하게), anchor_hints(Top10), candidate_pool
- 주의: 패턴을 강제해 EV를 깎지 않도록 “보조/미세조정” 전용
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase

class EngineVPA1(EngineBase):
    def __init__(self):
        super().__init__("VPA1")
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        out = {i: 0.5 for i in range(1, 46)}
        # 약한 밴드 앵커 점수화 스터브
        return out
