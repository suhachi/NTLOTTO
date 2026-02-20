from typing import Dict, List, Set, Tuple, Optional
import pandas as pd
import numpy as np
from .constants import EXCLUDE_CSV, K_EVAL
from .ssot import load_exclude_rounds

def compute_recall_at_k(topk: List[int], winning_six: Set[int]) -> float:
    """
    Calculate Recall@K = |TopK ∩ Win| / 6
    """
    if not winning_six:
        return 0.0
    common = set(topk).intersection(winning_six)
    return len(common) / 6.0

def update_engine_kpi(
    kpi_csv_path: str,
    engine_topk_by_round: Dict[str, Dict[int, List[int]]], 
    ssot_sorted_df: pd.DataFrame,
    exclusions: Set[int],
    k_eval: int = 20,
    windows: Tuple[int, int, int] = (10, 20, 30)
) -> pd.DataFrame:
    """
    Update Engine KPI (Recall@K) for all engines.
    
    Args:
        kpi_csv_path: Path to current KPI CSV (to load previous state or just structure, functionality mostly rebuilds or appends).
                      However, to compute 'Recent 30', we need history. 
                      Here we assume 'engine_topk_by_round' HAS identifying history.
        engine_topk_by_round: { 'NT4': { 1200: [..], 1201: [..], ... }, ... }
        ssot_sorted_df: SSOT DataFrame (for winning numbers).
        exclusions: Set of round numbers to exclude from KPI aggregation.
        
    Returns:
        DataFrame with columns: engine_id, overall, recent10, recent20, recent30, n_eval_rounds
    """
    
    # 1. Build Round-Wise Recall History per Engine
    # Map: Engine -> [(Round, Recall), ...]
    engine_recalls: Dict[str, List[float]] = {eng: [] for eng in engine_topk_by_round.keys()}
    
    # Convert SSOT to dict for fast lookup: Round -> Set(Winning 6)
    # Filter SSOT to only rounds relevant (we might have topk for future rounds? No, only past).
    ssot_valid = ssot_sorted_df[~ssot_sorted_df['round'].isin(exclusions)]
    winning_map = {
        row['round']: set([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
        for _, row in ssot_valid.iterrows()
    }

    # Iterate engines
    for engine, history in engine_topk_by_round.items():
        # history is Round -> TopK List
        # Sort rounds
        sorted_rounds = sorted(history.keys())
        
        for r_num in sorted_rounds:
            if r_num in exclusions:
                continue # Skip excluded rounds for KPI stats
            
            if r_num not in winning_map:
                continue # Can't score if no winning numbers (e.g. future round)
                
            win_set = winning_map[r_num]
            topk = history[r_num]
            
            recall = compute_recall_at_k(topk[:k_eval], win_set)
            engine_recalls[engine].append(recall)
            
    # 2. aggregating
    rows = []
    
    for engine, recalls in engine_recalls.items():
        n = len(recalls)
        if n == 0:
            row = {
                "engine_id": engine, 
                "status": "STUB",
                "overall": 0.0, 
                "recent10": 0.0, 
                "recent20": 0.0, 
                "recent30": 0.0, 
                "n_eval_rounds": 0
            }
        else:
            rec_arr = np.array(recalls)
            row = {
                "engine_id": engine,
                "status": "ACTIVE",
                "overall": float(np.mean(rec_arr)),
                "recent10": float(np.mean(rec_arr[-windows[0]:])),
                "recent20": float(np.mean(rec_arr[-windows[1]:])),
                "recent30": float(np.mean(rec_arr[-windows[2]:])),
                "n_eval_rounds": n
            }
        rows.append(row)
        
    return pd.DataFrame(rows)
