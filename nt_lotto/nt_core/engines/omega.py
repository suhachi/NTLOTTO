from __future__ import annotations
import pandas as pd
from typing import Dict
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class OmegaEngine(Engine):
    name = "NT-Ω"
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int, engine_outputs: Dict[str, EngineOutput] = None) -> EngineOutput:
        if not engine_outputs: return EngineOutput(scores=pd.DataFrame({"score": 0.0}, index=range(1, 46)))
        parts = []
        for name, w in self.weights.items():
            if name in engine_outputs:
                s = _z(engine_outputs[name].scores["score"])
                parts.append(w*s)
        total = sum(parts) if parts else pd.Series(0.0, index=range(1, 46))
        return EngineOutput(scores=pd.DataFrame({"score": total}))

def _z(s: pd.Series) -> pd.Series:
    m, sd = s.mean(), s.std()
    return (s - m) / sd if sd != 0 else s * 0
