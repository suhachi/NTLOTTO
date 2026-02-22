"""
[NT-PAT 엔진 정의]
- 역할: pair/간격/전이 등 패턴 탐지 + 커버리지(누락 방지) 힌트 제공
- 입력: ssot_sorted + ssot_ordered(전이)
- 출력: hint_pool(Top10~20), diagnostics(Top pairs/top transitions)
- 기본 모드: hint_only (score_map은 0 또는 매우 약하게)
- 금지: PAT 단독으로 메인 score를 지배하도록 설계 금지
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase

class EnginePAT(EngineBase):
    def __init__(self):
        super().__init__("PAT")
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        # 보조 힌트 전용 스터브 (모두 0)
        return {i: 0.0 for i in range(1, 46)}
