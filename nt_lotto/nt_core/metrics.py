from typing import Set, Dict, List, Union
import pandas as pd
import numpy as np

def recall_at_k(topk_set: Set[int], win_set: Set[int]) -> float:
    """
    Calculate Recall@K = |TopK ∩ Win| / 6
    """
    if not win_set:
        return 0.0
    
    intersection = len(topk_set.intersection(win_set))
    return intersection / 6.0

def summarize_recalls(recalls: List[float]) -> Dict[str, float]:
    """
    Summarize recall list into Overall, Recent10, Recent20, Recent30.
    """
    if not recalls:
        return {
            "overall": 0.0,
            "recent10": 0.0,
            "recent20": 0.0,
            "recent30": 0.0
        }
    
    n = len(recalls)
    recalls_arr = np.array(recalls)
    
    return {
        "overall": float(np.mean(recalls_arr)),
        "recent10": float(np.mean(recalls_arr[-10:])) if n >= 10 else float(np.mean(recalls_arr[-10:])),
        "recent20": float(np.mean(recalls_arr[-20:])) if n >= 20 else float(np.mean(recalls_arr[-20:])),
        "recent30": float(np.mean(recalls_arr[-30:])) if n >= 30 else float(np.mean(recalls_arr[-30:]))
    }
