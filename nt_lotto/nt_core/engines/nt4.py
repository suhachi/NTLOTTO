from __future__ import annotations
import pandas as pd
import numpy as np
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput

class NT4ExplorationEngine(Engine):
    """
    NT4: Exploration Engine (Contract v1.0)
    Combines NT5 logic with low-frequency exploration bonus.
    """
    name = "NT4"
    uses_sorted = True
    uses_ordered = False

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        df = feats.num_features.copy()
        
        # Baseline: Hot (ew_freq) + Mean Revert (-gap_z)
        base = _z(df["ew_freq"]) + 0.5 * _z(df["gap_z"].fillna(0.0))
        
        # Exploration: Bonus for numbers that haven't appeared in last 20 rounds
        f20 = df.get("freq_20", 0.0)
        expl_bonus = (f20 == 0).astype(float) * 1.5
        
        # Random noise for tie-breaking (reproducible)
        np.random.seed(t_end)
        noise = np.random.normal(0, 0.05, size=len(df))
        
        score = base + expl_bonus + noise
        
        return EngineOutput(
            engine=self.name,
            scores=pd.DataFrame({"score": score}, index=df.index),
            meta={'expl_n': int(expl_bonus.sum())},
            topk_diag={}
        )

def _z(s: pd.Series) -> pd.Series:
    if s.std() == 0: return s * 0.0
    return (s - s.mean()) / s.std()
