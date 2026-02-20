# nt_core/omega_fit.py
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import pandas as pd
from .schema import SSOT, FeaturePack, EngineOutput

@dataclass
class EnginePerf:
    name: str
    mean_all: float
    mean_last10: float
    mean_last20: float
    mean_last30: float
    perf_score: float

def softmax_weights(perf: Dict[str, float], gamma: float = 2.0) -> Dict[str, float]:
    keys = list(perf.keys())
    vals = [perf[k] for k in keys]
    m = max(vals) if vals else 0.0
    exps = [math.exp(gamma * (v - m)) for v in vals]
    s = sum(exps) if exps else 1.0
    return {k: e / s for k, e in zip(keys, exps)}

def summarize_engine_perf(per_round: pd.DataFrame, w_all=0.2, w10=0.3, w20=0.3, w30=0.2) -> EnginePerf:
    def tail_mean(n: int) -> float:
        t = per_round["recall_at_k"].tail(n)
        return float(t.mean()) if len(t) else float("nan")

    mean_all = float(per_round["recall_at_k"].mean()) if len(per_round) else float("nan")
    mean10 = tail_mean(10)
    mean20 = tail_mean(20)
    mean30 = tail_mean(30)

    def nz(x: float) -> float:
        return 0.0 if (x is None or pd.isna(x)) else float(x)

    perf_score = (
        w_all * nz(mean_all) +
        w10  * nz(mean10) +
        w20  * nz(mean20) +
        w30  * nz(mean30)
    )
    return EnginePerf(name="", mean_all=mean_all, mean_last10=mean10, mean_last20=mean20, mean_last30=mean30, perf_score=perf_score)

def omega_topk(ssot: SSOT, t_end: int, engine_outputs: Dict[str, EngineOutput], omega_weights: Dict[str, float], k: int = 20) -> List[int]:
    parts = []
    for name, w in omega_weights.items():
        if name not in engine_outputs: continue
        s = _z(engine_outputs[name].scores["score"])
        parts.append(float(w) * s)
    if not parts: raise ValueError("No engine outputs for omega_topk")
    total = sum(parts).sort_values(ascending=False)
    return total.index.astype(int).tolist()[:k]

def _z(s: pd.Series) -> pd.Series:
    m, sd = s.mean(), s.std()
    if sd == 0 or pd.isna(sd): return s*0
    return (s - m) / sd
