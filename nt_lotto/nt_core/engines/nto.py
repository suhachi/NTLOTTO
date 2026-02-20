from __future__ import annotations
import pandas as pd
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class NTOEngine(Engine):
    """
    NTO: Trend Reversion Hybrid (Contract v1.0)
    Combines momentum (frequency) and mean-reversion (gap).
    """
    name = "NTO"
    uses_sorted = True
    uses_ordered = False

    def __init__(self, p_trend=0.5, lam=0.7):
        # p_trend: weight for trend vs revert. lam: penalty for high-freq numbers in reversion.
        self.p_trend, self.lam = p_trend, lam

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        df = feats.num_features.copy()
        
        # 1. Trend Score: Hot numbers keep coming
        trend = _z(df["ew_freq"])
        
        # 2. Reversion Score: Long gap numbers are due
        revert = _z(df["gap_z"].fillna(0.0)) - self.lam * _z(df["ew_freq"])
        
        final_score = self.p_trend * trend + (1.0 - self.p_trend) * revert
        
        return EngineOutput(
            engine=self.name,
            scores=pd.DataFrame({"score": final_score}, index=df.index),
            meta={'p_trend': self.p_trend, 'lam': self.lam},
            topk_diag={}
        )

def _z(s: pd.Series) -> pd.Series:
    if s.std() == 0: return s * 0.0
    return (s - s.mean()) / s.std()
