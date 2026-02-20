from __future__ import annotations
import pandas as pd
import numpy as np
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class NTLL(Engine):
    name = "NT-LL"
    uses_sorted = True
    def score_numbers(self, ssot, feats, t_end):
        shape = feats.shape_stats
        if not shape: return EngineOutput(self.name, pd.DataFrame({"score": 0.0}, index=range(1,46)), {}, {})
        # Target most likely odd/even count
        patterns = pd.DataFrame(shape['pattern_counts'])
        best = patterns.loc[patterns['prob'].idxmax()]
        target_odd = best['odd_count']
        num_scores = pd.Series(0.0, index=range(1, 46))
        for n in num_scores.index:
            if target_odd >= 3 and n % 2 != 0: num_scores[n] += 1.0
            elif target_odd < 3 and n % 2 == 0: num_scores[n] += 1.0
        return EngineOutput(self.name, pd.DataFrame({"score": _z(num_scores)}, index=num_scores.index), {'target_odd': int(target_odd)}, {})

class NTPAT(Engine):
    name = "NT-PAT"
    uses_sorted = True
    def score_numbers(self, ssot, feats, t_end):
        # Repetition pattern from last 3 rounds
        last3 = ssot.sorted_df[ssot.sorted_df["round"] > t_end - 3]
        wins = last3[["n1","n2","n3","n4","n5","n6"]].values.flatten()
        counts = pd.Series(wins).value_counts()
        num_scores = pd.Series(0.0, index=range(1, 46))
        for n, c in counts.items():
            if 1 <= n <= 45: num_scores[n] = float(c)
        return EngineOutput(self.name, pd.DataFrame({"score": _z(num_scores)}, index=num_scores.index), {'history_len': 3}, {})

class NTHCE(Engine):
    name = "NT-HCE"
    uses_sorted = True
    def score_numbers(self, ssot, feats, t_end):
        df = feats.num_features
        mid = df["ew_freq"].mean()
        # High score for extreme hot/cold
        score = (df["ew_freq"] - mid).abs()
        return EngineOutput(self.name, pd.DataFrame({"score": _z(score)}, index=df.index), {}, {})

class NTDPP(Engine):
    name = "NT-DPP"
    uses_sorted = True
    def score_numbers(self, ssot, feats, t_end):
        # Diversity: Smoothing density
        f5 = feats.num_features.get("freq_5", 0.0)
        density = f5.rolling(window=3, center=True).mean().fillna(f5)
        return EngineOutput(self.name, pd.DataFrame({"score": _z(density)}, index=f5.index), {}, {})

def _z(s):
    if s.std() == 0: return s * 0.0
    return (s - s.mean()) / s.std()
