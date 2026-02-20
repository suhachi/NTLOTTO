from __future__ import annotations
import pandas as pd
from .base import Engine
from ..schema import SSOT, FeaturePack, EngineOutput
from ..features import band_of

class NTLL_ProxyEngine(Engine):
    name = "NT-LL"
    def __init__(self, band_target=(2,1,1,2,0.5)):
        self.band_target = band_target

    def score_numbers(self, ssot: SSOT, feats: FeaturePack, t_end: int) -> EngineOutput:
        idx = feats.num_features.index.astype(int)
        band_w = {i+1: self.band_target[i] for i in range(5)}
        w = pd.Series([band_w[band_of(n)] for n in idx], index=idx)
        w = (w - w.min()) / (w.max() - w.min() + 1e-9)
        return EngineOutput(scores=pd.DataFrame({"score": w}, index=idx))
