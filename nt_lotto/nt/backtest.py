from __future__ import annotations
import pandas as pd
from typing import List, Dict
from .schema import SSOT, BacktestResult, EngineOutput
from .features import build_feature_pack
from .metrics import recall_at_k

def walk_forward_backtest(ssot: SSOT, engine, rounds: List[int], k: int = 20) -> BacktestResult:
    rows = []
    sorted_df = ssot.sorted_df.set_index("round")
    for i, t_end in enumerate(rounds[:-1]):
        t_test = rounds[i+1]
        feats = build_feature_pack(ssot, t_end=t_end)
        out = engine.score_numbers(ssot, feats, t_end=t_end)
        topk = engine.topk(out, k=k)
        truth = set(sorted_df.loc[t_test, ["n1","n2","n3","n4","n5","n6"]].astype(int).tolist())
        rec = recall_at_k(topk, truth)
        rows.append({"round_train_end": t_end, "round_test": t_test, "recall_at_k": rec, "topk": topk})
    per_round = pd.DataFrame(rows)
    summary = _summarize_recalls(per_round, k)
    return BacktestResult(per_round=per_round, summary=summary)

def _summarize_recalls(per_round: pd.DataFrame, k: int) -> Dict[str, float]:
    if per_round.empty: return {"k": k, "n_tests": 0}
    def tail_mean(n: int) -> float:
        return float(per_round["recall_at_k"].tail(n).mean())
    return {
        "k": float(k), "n_tests": float(len(per_round)),
        "mean_recall_all": float(per_round["recall_at_k"].mean()),
        "mean_recall_last10": tail_mean(10),
        "mean_recall_last20": tail_mean(20),
        "mean_recall_last30": tail_mean(30),
    }

def latest_topk(ssot: SSOT, engine, k: int = 20) -> list[int]:
    rounds = sorted(ssot.sorted_df["round"].tolist())
    t_end = rounds[-1]
    feats = build_feature_pack(ssot, t_end=t_end)
    out = engine.score_numbers(ssot, feats, t_end=t_end)
    return engine.topk(out, k=k)
