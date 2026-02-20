from __future__ import annotations
import pandas as pd
import numpy as np

"""
NT5 Cluster Engine
Role: Multi-Window Hot-Cluster & Recency
Input: ssot_sorted.csv
Output: TopK(20) candidates
"""

def analyze(df_sorted: pd.DataFrame, target_round: int) -> list[int]:
    """
    NT5 Analysis Logic
    
    Features:
    - Hot30(n), Hot50(n), Hot100(n): Normalized frequency in recent K rounds
    - Recency indicators: 
        - In Last 5 (R5): 1.0 if present, else 0.0
        - In Last 10 (R10): 1.0 if present, else 0.0
        - In Last 1 (R1): 1.0 if present (mild penalty target), else 0.0
        
    Score Formula:
    Score = 0.3*Hot30 + 0.2*Hot50 + 0.15*Hot100 + 0.2*I[R5] + 0.15*I[R10] - 0.1*I[R1_ONLY]
    
    Tie-break: Score DESC, Number ASC
    """
    # 1. Filter Data (Use only past data)
    history = df_sorted[df_sorted['round'] < target_round]
    
    if history.empty:
        return []

    # Helper to clean and reindex (1-45 counts)
    def get_counts(data, rounds=None):
        if rounds:
            data = data.tail(rounds)
        vals = data.iloc[:, 1:7].values.flatten()
        return pd.Series(vals).value_counts().reindex(range(1, 46), fill_value=0)

    # 2. Extract Features
    # 2.1 Hot Windows
    hot30 = get_counts(history, 30)
    hot50 = get_counts(history, 50)
    hot100 = get_counts(history, 100)
    
    # 2.2 Recency Indicators
    # R5
    r5_data = history.tail(5)
    r5_vals = set(r5_data.iloc[:, 1:7].values.flatten())
    i_r5 = pd.Series([1.0 if n in r5_vals else 0.0 for n in range(1, 46)], index=range(1, 46))
    
    # R10
    r10_data = history.tail(10)
    r10_vals = set(r10_data.iloc[:, 1:7].values.flatten())
    i_r10 = pd.Series([1.0 if n in r10_vals else 0.0 for n in range(1, 46)], index=range(1, 46))

    # R1 (Last Round only)
    r1_data = history.tail(1)
    if not r1_data.empty:
        r1_vals = set(r1_data.iloc[:, 1:7].values.flatten())
        i_r1 = pd.Series([1.0 if n in r1_vals else 0.0 for n in range(1, 46)], index=range(1, 46))
    else:
        i_r1 = pd.Series(0.0, index=range(1, 46))

    # 3. Normalize (MinMax)
    def normalize(s):
        if s.max() == s.min():
            return s * 0.0
        return (s - s.min()) / (s.max() - s.min())

    norm_h30 = normalize(hot30)
    norm_h50 = normalize(hot50)
    norm_h100 = normalize(hot100)
    
    # Recency indicators are already 0.0 or 1.0, so normalization is identity if mixed, or 0 if all 0.
    # Strictly speaking they are binary, so they are inherently normalized in 0-1 scale.
    
    # 4. Compute Score
    # Weights
    A1, A2, A3 = 0.30, 0.20, 0.15
    A4, A5 = 0.20, 0.15
    A6 = 0.10 # Penalty
    
    final_score = (A1 * norm_h30) + (A2 * norm_h50) + (A3 * norm_h100) + \
                  (A4 * i_r5) + (A5 * i_r10) - (A6 * i_r1)
                  
    # 5. Deterministic Sort
    scores = pd.DataFrame({'score': final_score})
    scores['number'] = scores.index
    scores = scores.sort_values(by=['score', 'number'], ascending=[False, True])
    
    # 6. Select Top 20
    return scores.head(20)['number'].tolist()

