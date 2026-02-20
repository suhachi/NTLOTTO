from __future__ import annotations
import pandas as pd
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class NT4Engine(Engine):
    name = "NT4"
    def __init__(self, a=0.55, b=0.35, c=0.10):
        self.a, self.b, self.c = a, b, c

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        df = feats.num_features.copy()
        inv_ew = _z(1.0 - df["ew_freq"])
        score = self.a * _z(df["gap_z"].fillna(0.0)) + self.b * inv_ew + self.c * _z(df["bonus_freq_50"])
        return EngineOutput(scores=pd.DataFrame({"score": score}, index=df.index))

def _z(s: pd.Series) -> pd.Series:
    m, sd = s.mean(), s.std()
    return (s - m) / sd if sd != 0 else s * 0
