from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .schema import SSOT, BacktestResult, EngineOutput, BacktestRoundResult
from .features import build_feature_pack
from .metrics import recall_at_k

def run_backtest(ssot: SSOT, engine_inst: Any, rounds: List[int], k: int = 20) -> BacktestResult:
    """
    Standard Walk-Forward Backtest (Contract 2.3)
    """
    results_list = []
    sorted_df = ssot.sorted_df.set_index("round")
    
    # Engine requires either sorted or ordered via Contract flags
    # We pass BOTH in SSOT to engine_inst.score_numbers(ssot, ...)
    
    for i, t_end in enumerate(rounds[:-1]):
        t_test = rounds[i+1]
        
        # 1. Build Features up to t_end
        # engines might use different state modes, but for backtest we use a stable default or engine-specific one
        # For simplicity, we use the engine's preferred mode if it has one
        state_mode = getattr(engine_inst, 'preferred_state_mode', 'band_parity')
        feats = build_feature_pack(ssot, t_end=t_end, use_state=state_mode)
        
        # 2. Score
        out: EngineOutput = engine_inst.score_numbers(ssot, feats, t_end=t_end)
        
        # 3. Top K
        topk = out.scores.sort_values("score", ascending=False).index[:k].tolist()
        
        # 4. Evaluate
        truth = set(sorted_df.loc[t_test, ["n1","n2","n3","n4","n5","n6"]].astype(int).tolist())
        hits = len(set(topk) & truth)
        recall = hits / 6.0
        
        results_list.append({
            'round': t_test,
            'hits': hits,
            'recall_at_k': recall,
            'topk': topk
        })
        
    per_round = pd.DataFrame(results_list)
    
    if per_round.empty:
        return BacktestResult(
            engine=engine_inst.name, k=k, per_round=per_round,
            mean_all=0.0, mean_last10=0.0, mean_last20=0.0, mean_last30=0.0
        )
    
    mean_all = float(per_round['recall_at_k'].mean())
    mean_l10 = float(per_round['recall_at_k'].tail(10).mean())
    mean_l20 = float(per_round['recall_at_k'].tail(20).mean())
    mean_l30 = float(per_round['recall_at_k'].tail(30).mean())
    
    return BacktestResult(
        engine=engine_inst.name,
        k=k,
        per_round=per_round,
        mean_all=mean_all,
        mean_last10=mean_l10,
        mean_last20=mean_l20,
        mean_last30=mean_l30
    )
