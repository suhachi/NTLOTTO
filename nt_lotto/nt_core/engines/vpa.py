from __future__ import annotations
import itertools
import pandas as pd
import math
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class VPAEngine(Engine):
    name = "VPA"
    def __init__(self, W=300, min_pair_count=3):
        self.W, self.min_pair_count = W, min_pair_count

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        # Use a larger window (300-600) as recommended for stability
        s = ssot.sorted_df[ssot.sorted_df["round"] <= t_end].tail(self.W)
        wins = s[["n1","n2","n3","n4","n5","n6"]].values.tolist()
        
        single = {i:0 for i in range(1,46)}; pair = {}
        for row in wins:
            for i in row: single[i] += 1
            for a,b in itertools.combinations(sorted(row),2):
                pair[(a,b)] = pair.get((a,b),0) + 1
        
        denom = max(1, len(wins)); p = {i: single[i]/denom for i in single}
        score = {i:0.0 for i in range(1,46)}
        
        for (a,b), c in pair.items():
            # Apply Filter: count(i,j) >= min_pair_count
            if c < self.min_pair_count: continue
            
            pa, pb = p[a], p[b]
            # Lift/PMI calculation for stability
            lift = (c/denom) / (pa*pb + 1e-12)
            pmi = math.log(max(lift, 1e-12))
            
            # Aggregate PMI to number level as centralized signal
            score[a] += pmi; score[b] += pmi
            
        out = pd.Series(score).sort_index()
        # Scale for cross-engine comparison
        out = (out - out.mean()) / (out.std() + 1e-9)
        return EngineOutput(scores=pd.DataFrame({"score": out}))

class NTVPA1Engine(VPAEngine):
    name = "NT-VPA-1"
