# nt_core/engines/al1.py
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

class AL1SlotEngine(Engine):
    """
    AL1 = 추첨순서 '슬롯(1~6구)'에서 상태(state)가 얼마나 자주 나오는지에만 기반
    """
    name = "AL1"

    def __init__(self, use_state="band_parity", slot_weights=None):
        self.use_state = use_state
        self.slot_weights = slot_weights or {"slot1":1, "slot2":1, "slot3":1, "slot4":1, "slot5":1, "slot6":1}

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        if feats.slot_state_probs is None:
            raise ValueError("FeaturePack.slot_state_probs missing")

        slot_df = feats.slot_state_probs
        idx = feats.num_features.index.astype(int)
        states = [self._state(n) for n in idx]

        scores = []
        for st in states:
            if st in slot_df.index:
                val = 0.0
                for col, w in self.slot_weights.items():
                    val += float(slot_df.loc[st, col]) * float(w)
                scores.append(val)
            else:
                scores.append(0.0)

        s = pd.Series(scores, index=idx, dtype=float)
        out = pd.DataFrame({"score": _z(s)}, index=idx)
        return EngineOutput(scores=out)

    def _state(self, n: int) -> str:
        b = band_of(n)
        if self.use_state == "band": return f"B{b}"
        if self.use_state == "band_parity": return f"B{b}_{'O' if n%2 else 'E'}"
        if self.use_state == "band_tail": return f"B{b}_T{n%10}"
        return f"B{b}"
