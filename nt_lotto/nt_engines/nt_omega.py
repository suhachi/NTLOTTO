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
    # Omega can maintain a small internal momentum or just pass through NTO if it's purely a selector
    omega_scores = {}
    for n in range(1, 46):
        # Default pass-through in this implementation
        # The true power of Omega is selecting the final combinations, which is excluded from this scope.
        omega_scores[n] = float(base_scores.get(n, 0.5))
        
    # 3. Format Output
    results = []
    for n in range(1, 46):
        results.append({
            "n": n,
            "score": omega_scores[n],
            "evidence": ["Omega base score matched from NTO"]
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
