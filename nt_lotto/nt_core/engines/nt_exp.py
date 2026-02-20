from __future__ import annotations
import pandas as pd
import numpy as np
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class NTExplorationEngine(Engine):
    """
    NT-EXP: Exploration Engine (Contract v1.0)
    Focuses on 'Zero Frequency' and 'Cold' numbers in the last 10 rounds.
    """
    name = "NT-EXP"
    uses_sorted = True
    uses_ordered = False

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        df = feats.num_features.copy()
        
        # 1. Zero freq penalty: prioritize numbers with 0 freq in last 10
        f10 = df.get("freq_10", 0.0)
        zero_mask = (f10 == 0).astype(float)
        
        # 2. Within zero-freq, prioritize those with higher GAP (Mean reversion of the cold)
        gap_score = df["gap_z"].fillna(0.0)
        
        # 3. Add some randomness/exploration noise
        np.random.seed(t_end) # deterministic noise for backtest reproducibility
        noise = np.random.normal(0, 0.1, size=len(df))
        
        # Score = high if zero_freq + high_gap
        score = zero_mask * 2.0 + gap_score + noise
        
        return EngineOutput(
            engine=self.name,
            scores=pd.DataFrame({"score": score}, index=df.index),
            meta={'n_zeros': int(zero_mask.sum())},
            topk_diag={}
        )
