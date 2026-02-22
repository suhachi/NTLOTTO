from __future__ import annotations
import pandas as pd
from ..engines.base import EngineBase

def evaluate_engines_k(engines: dict[str, EngineBase], df_s: pd.DataFrame, df_o: pd.DataFrame, k: int=20, n: int=50) -> dict:
    """
    과거 N회차에 대해 K개의 추천 번호를 뽑았을 때 Recall(당첨 번호 포함 비율)을 평가
    (Lookahead 방지를 위해 매 회차마다 직전 데이터까지만 사용하여 평가)
    """
    df_s = df_s.sort_values("round").reset_index(drop=True)
    
    results = {name: {"hits": [], "bonus_hits": []} for name in engines}
    
    # 마지막 N회차 순회
    eval_start_idx = max(1, len(df_s) - n)
    for i in range(eval_start_idx, len(df_s)):
        # i회차를 맞히기 위해 i-1회차까지의 데이터만 제공
        past_s = df_s.iloc[:i]
        
        target_row = df_s.iloc[i]
        win_nums = set(int(target_row[f"n{j}"]) for j in range(1, 7))
        bonus = int(target_row["bonus"])
        
        # 엔진별 평가
        for name, eng in engines.items():
            # mock evaluation (속도를 위해 간이 사용)
            score_map = eng.score_map(past_s, df_o.iloc[:i]) 
            sorted_nums = sorted(score_map.items(), key=lambda x: -x[1])
            top_k = set(num for num, score in sorted_nums[:k])
            
            hits = len(win_nums & top_k)
            b_hit = 1 if bonus in top_k else 0
            
            results[name]["hits"].append(hits)
            results[name]["bonus_hits"].append(b_hit)
            
    # 통계 요약
    summary = {}
    import numpy as np
    for name in engines:
        h = results[name]["hits"]
        b = results[name]["bonus_hits"]
        summary[name] = {
            "recall_mean": float(np.mean(h)) / 6.0 if h else 0.0,
            "bonus_hit_rate": float(np.mean(b)) if b else 0.0,
            "mean_hits": float(np.mean(h)) if h else 0.0
        }
        
    return summary
