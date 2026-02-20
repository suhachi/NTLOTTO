from __future__ import annotations
import pandas as pd
import numpy as np

"""
NT-LL Local Deviation Correction Engine
Role: Local Deviation Correction (지역 편차 보정)
Input: ssot_sorted.csv
Output: TopK(20) candidates
"""

def analyze(df_sorted: pd.DataFrame, target_round: int) -> list[int]:
    """
    NT-LL Logic
    - For each number n (1~45):
        1. Compute global frequency (전체 빈도)
        2. Compute local frequency (최근 10회)
        3. Deviation = local - global (정규화)
        4. Correction: score = -|Deviation| (편차가 작을수록 점수 높음)
        5. Optionally, apply mild boost for numbers with local > global (상승세)
    - Deterministic: Score DESC, Number ASC
    """
    # 1. Filter Data (Use only past data)
    history = df_sorted[df_sorted['round'] < target_round]
    if history.empty:
        return []

    def get_freq(data, rounds=None):
        if rounds:
            data = data.tail(rounds)
        vals = data.iloc[:, 1:7].values.flatten()
        return pd.Series(vals).value_counts().reindex(range(1, 46), fill_value=0)

    global_freq = get_freq(history)
    local_freq = get_freq(history, 10)

    # Normalize (MinMax)
    def normalize(s):
        if s.max() == s.min():
            return s * 0.0
        return (s - s.min()) / (s.max() - s.min())

    norm_global = normalize(global_freq)
    norm_local = normalize(local_freq)

    deviation = norm_local - norm_global
    # Correction: 편차가 작을수록(0에 가까울수록) 점수 높음
    correction_score = -np.abs(deviation)
    # 상승세 보정: local > global인 경우 +0.05 가산
    correction_score += (deviation > 0).astype(float) * 0.05

    scores = pd.DataFrame({'score': correction_score})
    scores['number'] = scores.index
    scores = scores.sort_values(by=['score', 'number'], ascending=[False, True])
    return scores.head(20)['number'].tolist()
