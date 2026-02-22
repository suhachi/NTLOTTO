"""
[NTO 메타 엔진 정의]
- 역할: 여러 신호를 섞는 통합축(메타)
- 입력: ssot_sorted, (선택) 다른 엔진 score_map
- 출력: score_map, candidate_pool
- 주의: 다른 엔진을 흡수해 결과가 동일해지는 현상 방지(선택 레이어에서 비중 통제)
"""
from __future__ import annotations

import pandas as pd
from .base import EngineBase
from .nt4 import EngineNT4
from .nt5 import EngineNT5
from .omega import EngineOmega

class EngineNTO(EngineBase):
    def __init__(self):
        super().__init__("NTO")
        self.e4 = EngineNT4()
        self.e5 = EngineNT5()
        self.e_om = EngineOmega()
    
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        s4 = self.e4.score_map(df_s, df_o)
        s5 = self.e5.score_map(df_s, df_o)
        so = self.e_om.score_map(df_s, df_o)

        out = {}
        for i in range(1, 46):
            # 메타 가중합
            out[i] = (s4[i]*0.4 + s5[i]*0.4 + so[i]*0.2)
        mx = max(out.values()) if out else 1.0
        return {k: v/mx for k,v in out.items()}
