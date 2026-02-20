import pandas as pd
from typing import Dict, Any

"""
NT-Omega (NT-Ω) Engine
Role: Final Portfolio Selection Score Engine
* Strictly outputs Score Map & TopK (K_pool=22). No combinations generated here.
"""

def analyze(df_sorted: pd.DataFrame, round_r: int, *, k_eval: int = 20, k_pool: int = 22, **kwargs) -> Dict[str, Any]:
    # NT-Omega uses NTO as its base for integration
    from .nto import analyze as analyze_nto
    
    # Run NTO to get the meta score
    nto_result = analyze_nto(df_sorted, round_r, k_eval=45, **kwargs)
    
    # 1. Base Score Map
    if not nto_result.get('scores'):
        return {
            "engine": "NT-OMEGA", "round": round_r, "k_eval": k_eval,
            "params": {}, "scores": [], "topk": [], "metrics": {"status": "fallback"}
        }
        
    base_scores = {item['n']: item['score'] for item in nto_result['scores']}
    
    # 2. Omega specific adjustments (e.g., historical hits momentum)
    # Omega must NOT just pass through NTO if it's purely a selector, to avoid 100% Jaccard overlap.
    # Add an independent short-term momentum factor (last 10 rounds frequency).
    
    df_past = df_sorted[df_sorted['round'] < round_r].tail(10)
    freq_map = {1:0} # Fallback
    if not df_past.empty:
        vals = df_past[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.flatten()
        freq_map = pd.Series(vals).value_counts().to_dict()
        
    f_max = max(freq_map.values()) if freq_map else 1.0
    f_max = f_max if f_max > 0 else 1.0
    
    omega_scores = {}
    evidence_map = {}
    
    for n in range(1, 46):
        b_score = float(base_scores.get(n, 0.0))
        freq = freq_map.get(n, 0.0)
        norm_freq = freq / f_max
        
        # Apply lambda factor to momentum (e.g., 0.15)
        adj = 0.15 * norm_freq
        omega_scores[n] = b_score + adj
        evidence_map[n] = f"NTO Base({b_score:.3f}) + Momentum({adj:.3f})"
        
    # 3. Format Output
    results = []
    for n in range(1, 46):
        results.append({
            "n": n,
            "score": omega_scores[n],
            "evidence": [evidence_map[n]]
        })
        
    results.sort(key=lambda x: (-x['score'], x['n']))
    
    # Important: Omega extracts K_pool (22) typically, but we also return K_eval (20) depending on caller needs.
    # Contract dictates returning K_pool for Omega's main slice.
    topk_pool = [r['n'] for r in results[:k_pool]]
    
    return {
        "engine": "NT-OMEGA",
        "round": round_r,
        "k_eval": k_eval,
        "k_pool": k_pool,
        "params": nto_result.get('params', {}),
        "scores": results,
        "topk": topk_pool,
        "metrics": {"note": "Omega selection active. K_pool=22 returned."}
    }
