# nt_core/engines/alx.py
from __future__ import annotations
import pandas as pd
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

def _z(s: pd.Series) -> pd.Series:
    m, sd = s.mean(), s.std()
    if sd == 0 or pd.isna(sd):
        return s * 0
    return (s - m) / sd

class ALXHybridEngine(Engine):
    """
    ALX = AL1(Slot) + AL2(Markov) Hybrid
    """
    name = "ALX"

    def __init__(self, al1_engine, al2_engine, w1: float = 0.5, w2: float = 0.5):
        self.al1 = al1_engine
        self.al2 = al2_engine
        self.w1 = w1
        self.w2 = w2

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        out1 = self.al1.score_numbers(ssot, feats, t_end=t_end).scores["score"]
        out2 = self.al2.score_numbers(ssot, feats, t_end=t_end).scores["score"]

        s = self.w1 * _z(out1) + self.w2 * _z(out2)
        df = pd.DataFrame({"score": _z(s)}, index=s.index.astype(int))
        return EngineOutput(scores=df)
