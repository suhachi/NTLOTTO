# nt_core/engines/al2.py
from __future__ import annotations
import pandas as pd
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput
from ..features import band_of

def _z(s: pd.Series) -> pd.Series:
    m, sd = s.mean(), s.std()
    if sd == 0 or pd.isna(sd):
        return s*0
    return (s - m) / sd

class AL2MarkovEngine(Engine):
    """
    AL2 = 추첨순서 '전이(마코프)'만 기반
    """
    name = "AL2"

    def __init__(self, use_state="band_parity"):
        self.use_state = use_state

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        if feats.markov_state is None:
            raise ValueError("FeaturePack.markov_state missing")

        mk = feats.markov_state
        to_mass = mk.groupby("to")["p"].sum() if not mk.empty else pd.Series()

        idx = feats.num_features.index.astype(int)
        states = [self._state(n) for n in idx]
        s = pd.Series([float(to_mass.get(st, 0.0)) for st in states], index=idx, dtype=float)

        out = pd.DataFrame({"score": _z(s)}, index=idx)
        return EngineOutput(scores=out)

    def _state(self, n: int) -> str:
        b = band_of(n)
        if self.use_state == "band": return f"B{b}"
        if self.use_state == "band_parity": return f"B{b}_{'O' if n%2 else 'E'}"
        if self.use_state == "band_tail": return f"B{b}_T{n%10}"
        return f"B{b}"
