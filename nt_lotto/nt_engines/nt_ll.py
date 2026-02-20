from __future__ import annotations
import pandas as pd
import numpy as np

"""
NT-LL Local Deviation Correction Engine
Role: Local Deviation Correction (지역 편차 보정)
Input: ssot_sorted.csv
Output: TopK(20) candidates
"""

B_UNDER = 1.0
B_OVER = 0.8
W_SIZE = 20

def analyze(df_sorted: pd.DataFrame, round_r: int, *, k_eval: int = 20, **kwargs) -> dict:
    """
    NT-LL (Local Linear / Low-Lag Adjustment)
    
    Formula:
    fg(n) = (count_global(n) + 1) / (6 * len(H) + 45)
    fr(n) = (count_recent(n) + 1) / (6 * W + 45)
    dev(n) = norm(fr(n)) - norm(fg(n))
    score(n) = b_under * max(-dev(n), 0) - b_over * max(dev(n), 0)
    """
    
    # 1. Look-ahead Prevention
    df_past = df_sorted[df_sorted['round'] < round_r].copy()
    if not df_past.empty:
        assert df_past['round'].max() < round_r, "Look-ahead detected in NT-LL window slicing"
        
    if df_past.empty:
        return {
            "engine": "NT-LL", "round": round_r, "k_eval": k_eval,
            "params": {"W": W_SIZE, "b_under": B_UNDER, "b_over": B_OVER},
            "scores": [], "topk": []
        }

    # 2. Get counts (Numbers 1-45)
    def get_counts(df):
        vals = df.iloc[:, 1:7].values.flatten()
        return pd.Series(vals).value_counts().reindex(range(1, 46), fill_value=0)

    count_g = get_counts(df_past)
    recent_window = df_past.tail(W_SIZE)
    count_r = get_counts(recent_window)
    
    total_g = len(df_past)
    total_r = len(recent_window)
    
    # 3. Laplace Smoothing
    fg = (count_g + 1) / (6 * total_g + 45)
    fr = (count_r + 1) / (6 * total_r + 45)
    
    # 4. Normalization (MinMax)
    def normalize(s):
        s_min, s_max = s.min(), s.max()
        if s_max - s_min < 1e-12:
            return pd.Series(0.5, index=s.index)
        return (s - s_min) / (s_max - s_min + 1e-12)
    
    norm_g = normalize(fg)
    norm_r = normalize(fr)
    
    # 5. Deviation and Score
    dev = norm_r - norm_g
    
    scores_raw = {}
    for n in range(1, 46):
        d = dev[n]
        if d < 0:
            s = B_UNDER * (-d)
        else:
            s = -B_OVER * d
        scores_raw[n] = float(s)
        
    # 6. Final Result Construction
    results = []
    for n in range(1, 46):
        results.append({
            "n": n,
            "score": scores_raw[n],
            "dev": float(dev[n]),
            "f_recent": float(fr[n]),
            "f_prev": float(fg[n]) # 'f_prev' as used in spec for global/prior
        })
    
    # Tie-break: Score DESC, Number ASC
    # Sorting is done for the topk selection and also the returned scores list
    results.sort(key=lambda x: (-x['score'], x['n']))
    
    topk = [r['n'] for r in results[:k_eval]]
    
    return {
        "engine": "NT-LL",
        "round": round_r,
        "k_eval": k_eval,
        "params": {"W": W_SIZE, "b_under": B_UNDER, "b_over": B_OVER},
        "scores": results,
        "topk": topk
    }

