import pandas as pd
from typing import Dict, Any

"""
NT-VPA-1 Engine
Role: Hybrid of VPA pattern aggregation + NT-LL local deviation shrinkage
"""

def analyze(df_sorted: pd.DataFrame, round_r: int, *, k_eval: int = 20, **kwargs) -> Dict[str, Any]:
    # 1. Base VPA Score
    from .vpa import analyze as analyze_vpa
    
    # Exclude lookahead before calling VPA? 
    # VPA itself has lookahead prevention, but let's pass the same df
    df_past = df_sorted[df_sorted['round'] < round_r].copy()
    if df_past.empty:
        return {
            "engine": "NT-VPA-1", "round": round_r, "k_eval": k_eval,
            "params": {"alpha": 0.5}, "scores": [], "topk": []
        }
        
    vpa_result = analyze_vpa(df_past, round_r, k_eval=k_eval, **kwargs)
    if not vpa_result['scores']:
        return vpa_result # fallback
        
    vpa_scores = {item['n']: item for item in vpa_result['scores']}
    
    # 2. NT-LL Local Deviation (W=20)
    w_size = 20
    alpha = kwargs.get('alpha', 0.5)
    
    def get_counts(df):
        vals = df[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.flatten()
        return pd.Series(vals).value_counts().reindex(range(1, 46), fill_value=0)

    count_g = get_counts(df_past)
    recent_window = df_past.tail(w_size)
    count_r = get_counts(recent_window)
    
    total_g = max(len(df_past), 1)
    total_r = max(len(recent_window), 1)
    
    fg = (count_g + 1) / (6 * total_g + 45)
    fr = (count_r + 1) / (6 * total_r + 45)
    
    def normalize(s):
        s_min, s_max = s.min(), s.max()
        if s_max - s_min < 1e-12:
            return pd.Series(0.5, index=s.index)
        return (s - s_min) / (s_max - s_min + 1e-12)
        
    norm_g = normalize(fg)
    norm_r = normalize(fr)
    dev = norm_r - norm_g # positive means overheated locally
    
    # 3. Shrinkage & Stability
    final_results = []
    
    for n in range(1, 46):
        base_item = vpa_scores[n]
        v_score = base_item['score']
        d = dev[n]
        
        # Shrinkage: penalize if recently overheated
        penalty = alpha * max(0.0, float(d))
        new_score = v_score - penalty
        
        # Stability: smaller absolute deviation -> more stable
        stability = 1.0 - abs(float(d))
        
        evidence = list(base_item['evidence'])
        if penalty > 0:
            evidence.append(f"Penalty -{penalty:.3f} due to local over-frequency (+dev)")
            
        final_results.append({
            "n": n,
            "score": new_score,
            "stability": stability,
            "evidence": evidence
        })
        
    # 4. Sort and TopK
    final_results.sort(key=lambda x: (-x['score'], x['n']))
    topk = [r['n'] for r in final_results[:k_eval]]
    
    return {
        "engine": "NT-VPA-1",
        "round": round_r,
        "k_eval": k_eval,
        "params": {"alpha": alpha, "w_size": w_size},
        "scores": final_results,
        "topk": topk
    }
