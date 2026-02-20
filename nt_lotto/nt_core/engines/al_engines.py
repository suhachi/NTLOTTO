from __future__ import annotations
import pandas as pd
import numpy as np
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput
from ..features import band_of

class AL1(Engine):
    name = "AL1"
    uses_sorted = False
    uses_ordered = True
    def score_numbers(self, ssot, feats, t_end):
        slot_df = feats.slot_state_probs
        if slot_df is None: return EngineOutput(self.name, pd.DataFrame({"score": 0.0}, index=range(1,46)), {}, {})
        def get_st(n):
            b = band_of(n)
            return f"B{b}_{'O' if n%2 else 'E'}"
        num_scores = pd.Series(0.0, index=range(1, 46))
        for n in num_scores.index:
            st = get_st(n)
            if st in slot_df.index: num_scores[n] = slot_df.loc[st].sum()
        return EngineOutput(self.name, pd.DataFrame({"score": _z(num_scores)}, index=num_scores.index), {}, {})

class AL2(Engine):
    name = "AL2"
    uses_sorted = False
    uses_ordered = True
    def score_numbers(self, ssot, feats, t_end):
        markov_df = feats.markov_state
        if markov_df is None or markov_df.empty: return EngineOutput(self.name, pd.DataFrame({"score": 0.0}, index=range(1,46)), {}, {})
        last_row = ssot.ordered_df[ssot.ordered_df["round"] == t_end]
        if last_row.empty: return EngineOutput(self.name, pd.DataFrame({"score": 0.0}, index=range(1,46)), {}, {})
        last_nums = last_row[["b1","b2","b3","b4","b5","b6"]].values[0]
        def get_st(n): b = band_of(n); return f"B{b}_{'O' if n%2 else 'E'}"
        last_states = [get_st(n) for n in last_nums]
        num_scores = pd.Series(0.0, index=range(1, 46))
        for n in num_scores.index:
            target_st = get_st(n)
            for start_st in last_states:
                match = markov_df[(markov_df["from"] == start_st) & (markov_df["to"] == target_st)]
                if not match.empty: num_scores[n] += match["p"].values[0]
        return EngineOutput(self.name, pd.DataFrame({"score": _z(num_scores)}, index=num_scores.index), {'transitions': len(markov_df)}, {})

class ALX(Engine):
    name = "ALX"
    uses_sorted = True
    uses_ordered = True
    def score_numbers(self, ssot, feats, t_end):
        o1 = AL1().score_numbers(ssot, feats, t_end)
        o2 = AL2().score_numbers(ssot, feats, t_end)
        score = (o1.scores["score"] + o2.scores["score"]) / 2.0
        return EngineOutput(self.name, pd.DataFrame({"score": score}, index=score.index), {'components': ['AL1', 'AL2']}, {})

def _z(s):
    if s.std() == 0: return s * 0.0
    return (s - s.mean()) / s.std()
