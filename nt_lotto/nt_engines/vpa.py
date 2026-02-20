import pandas as pd
import numpy as np
from collections import defaultdict

"""
VPA (Value-Pattern Aggregation) Engine
Role: Pattern Matching & Local Aggregation
"""

def get_band(n: int) -> int:
    if 1 <= n <= 9: return 1
    if 10 <= n <= 19: return 2
    if 20 <= n <= 29: return 3
    if 30 <= n <= 39: return 4
    if 40 <= n <= 45: return 5
    return 0

def get_ending(n: int) -> int:
    return n % 10

def get_even_odd(n: int) -> str:
    return "even" if n % 2 == 0 else "odd"

def analyze(df_sorted: pd.DataFrame, round_r: int, *, k_eval: int = 20, **kwargs) -> dict:
    # default parameters
    window_set = kwargs.get('window_set', [3, 5, 10, 20])
    fw = kwargs.get('feature_weights', {
        'band_dev': 0.3,
        'ending_dev': 0.3,
        'even_odd_dev': 0.1,
        'pair_co_occurrence': 0.3
    })
    
    df_past = df_sorted[df_sorted['round'] < round_r].copy()
    if not df_past.empty:
        assert df_past['round'].max() < round_r, "Look-ahead bias detected in VPA"
        
    if df_past.empty:
        return {
            "engine": "VPA", "round": round_r, "k_eval": k_eval,
            "params": {"window_set": window_set, "weights": fw},
            "scores": [], "topk": []
        }

    total_past = len(df_past)
    
    # Global baselines
    global_counts = {n: 0 for n in range(1, 46)}
    global_bands = {1:0, 2:0, 3:0, 4:0, 5:0}
    global_endings = {e: 0 for e in range(10)}
    global_eo = {'even': 0, 'odd': 0}
    
    vals = df_past[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.flatten()
    for v in vals:
        if 1 <= v <= 45:
            global_counts[v] += 1
            global_bands[get_band(v)] += 1
            global_endings[get_ending(v)] += 1
            global_eo[get_even_odd(v)] += 1
            
    # Smoothing / Expected Ratios
    def expected_ratio(count, total_count, options):
        # Laplace
        return (count + 1) / (total_count + options)

    p_band_exp = {b: expected_ratio(global_bands[b], total_past * 6, 5) for b in global_bands}
    p_end_exp = {e: expected_ratio(global_endings[e], total_past * 6, 10) for e in global_endings}
    p_eo_exp = {k: expected_ratio(global_eo[k], total_past * 6, 2) for k in global_eo}

    final_scores = {n: 0.0 for n in range(1, 46)}
    evidence_map = defaultdict(list)
    
    # Process each window
    # Recency decay W -> weight
    w_sum = sum(1.0 / w for w in window_set)
    decay = {w: (1.0 / w) / w_sum for w in window_set}
    
    for w in window_set:
        recent = df_past.tail(w)
        if recent.empty: continue
        
        r_total = len(recent) * 6
        r_vals = recent[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.flatten()
        
        r_bands = {1:0, 2:0, 3:0, 4:0, 5:0}
        r_endings = {e: 0 for e in range(10)}
        r_eo = {'even': 0, 'odd': 0}
        
        # Pair co-occurrence matrix for window
        pair_matrix = np.zeros((46, 46))
        for _, row in recent.iterrows():
            nums = row.iloc[1:7].values
            for i in range(len(nums)):
                for j in range(i+1, len(nums)):
                    u, v = nums[i], nums[j]
                    if 1 <= u <= 45 and 1 <= v <= 45:
                        pair_matrix[u][v] += 1
                        pair_matrix[v][u] += 1
        
        for v in r_vals:
            if 1 <= v <= 45:
                r_bands[get_band(v)] += 1
                r_endings[get_ending(v)] += 1
                r_eo[get_even_odd(v)] += 1
                
        p_band_obs = {b: expected_ratio(r_bands[b], r_total, 5) for b in r_bands}
        p_end_obs = {e: expected_ratio(r_endings[e], r_total, 10) for e in r_endings}
        p_eo_obs = {k: expected_ratio(r_eo[k], r_total, 2) for k in r_eo}
        
        # Normalize dev logic: VPA boosts numbers belonging to underrepresented patterns
        # deviation = observed - expected. If obs < exp, dev is negative -> boost it? Or if we want trend momentum?
        # Value-Pattern *Aggregation*: We score based on momentum (Trend riding) OR mean reversion.
        # "최근 윈도우에서 관측되는 패턴 편차를 점수로 산출"
        # Let's define deviation as Obs - Exp. 
        # If mean reversion (like NT-LL): score = Exp - Obs (negative dev)
        # However, VPA usually looks for pattern *trends* or structural imbalances.
        # Let's say score = |Obs - Exp| to identify strong anomalies, 
        # but to give a directional score: we reward Mean Reversion as default (Obs < Exp => positive score).
        # We will follow the contract simply: Dev = Expected - Observed (underperforming patterns get positive score).
        
        dev_band = {b: p_band_exp[b] - p_band_obs[b] for b in p_band_exp}
        dev_end = {e: p_end_exp[e] - p_end_obs[e] for e in p_end_exp}
        dev_eo = {k: p_eo_exp[k] - p_eo_obs[k] for k in p_eo_exp}
        
        # MinMax norms per window to keep [0,1]
        def norm_dict(d):
            vmin, vmax = min(d.values()), max(d.values())
            if vmax - vmin < 1e-9: return {k: 0.5 for k in d}
            return {k: (v - vmin)/(vmax - vmin) for k, v in d.items()}
            
        n_band = norm_dict(dev_band)
        n_end = norm_dict(dev_end)
        n_eo = norm_dict(dev_eo)
        
        # Pair score: sum of co-occurrences with other numbers in this window
        pair_scores = {n: np.sum(pair_matrix[n]) for n in range(1, 46)}
        n_pair = norm_dict(pair_scores)
        
        # Combine
        for n in range(1, 46):
            b = get_band(n)
            e = get_ending(n)
            eo = get_even_odd(n)
            
            s = (fw['band_dev'] * n_band[b] + 
                 fw['ending_dev'] * n_end[e] + 
                 fw['even_odd_dev'] * n_eo[eo] + 
                 fw['pair_co_occurrence'] * n_pair[n])
            
            final_scores[n] += decay[w] * s
            
            if w == 5 and n_band[b] > 0.8:
                evidence_map[n].append(f"Strong band anomaly (+dev) in W=5")
            if w == 10 and n_pair[n] > 0.8:
                evidence_map[n].append(f"High pair co-occurrence in W=10")

    # Final normalization
    f_min, f_max = min(final_scores.values()), max(final_scores.values())
    
    results = []
    for n in range(1, 46):
        score_norm = 0.5
        if f_max - f_min > 1e-9:
            score_norm = (final_scores[n] - f_min) / (f_max - f_min)
        
        ev_list = evidence_map[n][:3] if evidence_map[n] else ["Average pattern fit"]
        
        results.append({
            "n": n,
            "score": float(score_norm),
            "evidence": ev_list
        })
        
    results.sort(key=lambda x: (-x['score'], x['n']))
    topk = [r['n'] for r in results[:k_eval]]
    
    return {
        "engine": "VPA",
        "round": round_r,
        "k_eval": k_eval,
        "params": {"window_set": window_set, "weights": fw},
        "scores": results,
        "topk": topk
    }
