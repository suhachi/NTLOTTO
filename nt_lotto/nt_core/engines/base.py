from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd
from typing import List
from ..schema import SSOT, FeaturePack, EngineOutput

from ..constants import K_DIAG, K_EVAL

class Engine(ABC):
    name: str
    uses_sorted: bool = True
    uses_ordered: bool = False 

    @abstractmethod
    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        raise NotImplementedError

    def get_output(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        out = self.score_numbers(ssot, feats, t_end)
        # Add TopK Diag
        topk_diag = {}
        for k in K_DIAG + [K_EVAL]:
            topk_diag[k] = out.scores.sort_values("score", ascending=False).index[:k].tolist()
        
        return EngineOutput(
            engine=self.name,
            scores=out.scores,
            meta=out.meta,
            topk_diag=topk_diag
        )
