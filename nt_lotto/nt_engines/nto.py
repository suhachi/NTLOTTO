import pandas as pd
from nt_lotto.nt_engines import registry
from typing import Dict, Any, List
import copy

"""
NTO (Integrative Meta Optimizer)
Role: Meta scoring aggregation based on existing engines.
"""

def analyze(df_sorted: pd.DataFrame, round_r: int, *, k_eval: int = 20, **kwargs) -> Dict[str, Any]:
    # NTO uses active implementations
    # Target active engines
    active_engine_names = ["NT4", "NT5", "NT-LL", "VPA", "NT-VPA-1"]
    
    # 1. Gather scores from engines
    from nt_lotto.scripts.run_engines import get_engine_stub_prediction
    engine_score_maps = {}
    
    # To prevent circular imports or huge overhead, we dynamically import the exact functions
    # Because evaluate/run_engines is already heavily patched, we replicate the load here
    # or rely on registry if it returns actual functions.
    # Currently registry returning functions is a bit hacky, let's import directly.
    import importlib
    
    df_past = df_sorted[df_sorted['round'] < round_r].copy()
    if df_past.empty:
         return {"engine": "NTO", "round": round_r, "topk": [], "scores": []}
         
    for en_name in active_engine_names:
        mod_name = en_name.lower().replace("-", "_")
        try:
            mod = importlib.import_module(f"nt_lotto.nt_engines.{mod_name}")
            result = mod.analyze(df_past, round_r, k_eval=k_eval)
            if isinstance(result, dict) and 'scores' in result:
                # Expecting score list of dicts: [{'n': 1, 'score': 0.8}, ...]
                s_map = {item['n']: item['score'] for item in result['scores']}
                engine_score_maps[en_name] = s_map
        except Exception as e:
            # Fallback or stub
            pass

    # 2. Score Aggregation (Weighted Sum)
    weights = kwargs.get('engine_weights', {
        "NT4": 1.0, "NT5": 1.0, "NT-LL": 1.0, "VPA": 1.0, "NT-VPA-1": 1.0
    })
    
    meta_scores = {n: 0.0 for n in range(1, 46)}
    
    for en, smap in engine_score_maps.items():
        w = weights.get(en, 0.0)
        if w == 0: continue
        
        # Optional Calibration (MinMax)
        vals = list(smap.values())
        if not vals: continue
        vmin, vmax = min(vals), max(vals)
        
        for n in range(1, 46):
            raw = smap.get(n, 0.5)
            # z-score or minmax
            norm = (raw - vmin) / (vmax - vmin + 1e-9)
            meta_scores[n] += w * norm
            
    # 3. Format Output
    results = []
    for n in range(1, 46):
        results.append({
            "n": n,
            "score": meta_scores[n],
            "evidence": ["NTO Aggregation"]
        })
        
    results.sort(key=lambda x: (-x['score'], x['n']))
    topk = [r['n'] for r in results[:k_eval]]
    
    return {
        "engine": "NTO",
        "round": round_r,
        "k_eval": k_eval,
        "params": {"engine_weights": weights},
        "scores": results,
        "topk": topk,
        "engine_contributions": "Available in detailed metrics" # stub per contract
    }
