from __future__ import annotations
import pandas as pd
import numpy as np
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class VPA(Engine):
    name = "VPA"
    uses_sorted = True
    def score_numbers(self, ssot, feats, t_end):
        pair_df = feats.pair_stats
        if pair_df is None or pair_df.empty: return EngineOutput(self.name, pd.DataFrame({"score": 0.0}, index=range(1,46)), {}, {})
        # Use simple pair counts for VPA
        f10 = feats.num_features.get("freq_10", 0.0)
        anchors = f10.sort_values(ascending=False).index[:5].tolist()
        num_scores = pd.Series(0.0, index=range(1, 46))
        for anc in anchors:
            matches = pair_df[(pair_df["n1"] == anc) | (pair_df["n2"] == anc)]
            for _, row in matches.iterrows():
                other = int(row["n2"] if row["n1"] == anc else row["n1"])
                if 1 <= other <= 45: num_scores[other] += row["count"]
        return EngineOutput(self.name, pd.DataFrame({"score": _z(num_scores)}, index=num_scores.index), {'anchors': anchors}, {})

class NTVPA1(Engine):
    name = "NT-VPA-1"
    uses_sorted = True
    def score_numbers(self, ssot, feats, t_end):
        pair_df = feats.pair_stats # Use lift/pmi for "strong signal"
        if pair_df is None or pair_df.empty: return EngineOutput(self.name, pd.DataFrame({"score": 0.0}, index=range(1,46)), {}, {})
        latest_win = ssot.sorted_df[ssot.sorted_df["round"] == t_end][["n1","n2","n3","n4","n5","n6"]].values.flatten()
        num_scores = pd.Series(0.0, index=range(1, 46))
        for anc in latest_win:
            matches = pair_df[((pair_df["n1"] == anc) | (pair_df["n2"] == anc)) & (pair_df["lift"] > 1.2)]
            for _, row in matches.iterrows():
                other = int(row["n2"] if row["n1"] == anc else row["n1"])
                if 1 <= other <= 45: num_scores[other] += row["lift"]
        return EngineOutput(self.name, pd.DataFrame({"score": _z(num_scores)}, index=num_scores.index), {'threshold': 1.2}, {})

def _z(s):
    if s.std() == 0: return s * 0.0
    return (s - s.mean()) / s.std()
