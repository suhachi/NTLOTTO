from __future__ import annotations
import pandas as pd
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class NT5Engine(Engine):
    """
    NT5: Balanced Baseline (Contract v1.0)
    Weights: Long-term (ew), 20w, 10w, 5w, and Gap structure.
    """
    name = "NT5"
    uses_sorted = True
    uses_ordered = False

    def __init__(self, wL=0.10, w20=0.15, w10=0.25, w5=0.35, wg=0.15):
        self.wL, self.w20, self.w10, self.w5, self.wg = wL, w20, w10, w5, wg

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        df = feats.num_features.copy()
        
        s_L   = _z(df["ew_freq"])
        s_20  = _z(df.get("freq_20", 0.0))
        s_10  = _z(df.get("freq_10", 0.0))
        s_5   = _z(df.get("freq_5", 0.0))
        s_gap = df["gap_z"].fillna(0.0)
        
        score = (
            self.wL  * s_L +
            self.w20 * s_20 +
            self.w10 * s_10 +
            self.w5  * s_5 +
            self.wg  * s_gap
        )
        
        return EngineOutput(
            engine=self.name,
            scores=pd.DataFrame({"score": score}, index=df.index),
            meta={'weights': [self.wL, self.w20, self.w10, self.w5, self.wg]},
            topk_diag={} # Filled by base.get_output
        )

def _z(s: pd.Series) -> pd.Series:
    if s.std() == 0: return s * 0.0
    return (s - s.mean()) / s.std()
