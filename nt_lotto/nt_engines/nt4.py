from __future__ import annotations
import pandas as pd
import numpy as np

"""
NT4 Standard Engine
Role: Baseline (Frequency + Trend)
Input: ssot_sorted.csv
Output: TopK(20) candidates
"""

def analyze(df_sorted: pd.DataFrame, target_round: int) -> list[int]:
    """
    NT4 Analysis Logic
    
    Logic:
    1. Filter history < target_round
    2. Score = w_g * (Global Freq) + w_r * (Recent Freq) + w_t * (Trend)
    
    Weights (Default):
    - w_g (Global): 0.5
    - w_r (Recent 30): 0.3
    - w_t (Trend): 0.2
    
    Trend is defined as: (Freq Last 30) - (Freq Previous 30)
    """
    # 1. Filter Data (Use only past data)
    history = df_sorted[df_sorted['round'] < target_round]
    
    if history.empty:
        return []

    # 2. Extract Features
    # 2.1 Calculate Frequencies
    def get_freq(data, rounds=None):
        if rounds:
            data = data.tail(rounds)
        # Using columns n1..n6 (indices 1 to 6 usually, check SSOT structure)
        # SSOT Sorted columns: round, n1, n2, n3, n4, n5, n6, bonus
        vals = data.iloc[:, 1:7].values.flatten()
        return pd.Series(vals).value_counts().reindex(range(1, 46), fill_value=0)

    global_freq = get_freq(history)
    recent_freq = get_freq(history, 30)
    
    # Previous 30 for Trend
    prev_30_data = history.iloc[-60:-30] if len(history) >= 60 else pd.DataFrame()
    prev_freq = get_freq(prev_30_data) if not prev_30_data.empty else pd.Series(0, index=range(1, 46))
    
    trend = recent_freq - prev_freq

    # 3. Normalize (Min-Max Scaling to 0-1)
    def normalize(s):
        if s.max() == s.min():
            return s * 0.0
        return (s - s.min()) / (s.max() - s.min())

    norm_g = normalize(global_freq)
    norm_r = normalize(recent_freq)
    norm_t = normalize(trend)
    
    # 4. Compute Score
    # Weights
    W_G, W_R, W_T = 0.5, 0.3, 0.2
    
    final_score = (W_G * norm_g) + (W_R * norm_r) + (W_T * norm_t)
    
    # 5. Deterministic Sort (Score DESC, Number ASC)
    # Create DataFrame for sorting
    scores = pd.DataFrame({'score': final_score})
    scores['number'] = scores.index
    
    scores = scores.sort_values(by=['score', 'number'], ascending=[False, True])
    
    # 6. Select Top 20
    return scores.head(20)['number'].tolist()
