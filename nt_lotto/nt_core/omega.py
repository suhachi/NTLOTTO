import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from .schemas import EngineKPI, OmegaWeight, CandidateRow

# Locked Constraints
DEFAULT_COEFFS = {'a0': 0.25, 'a10': 0.35, 'a20': 0.25, 'a30': 0.15}
DEFAULT_TAU = 0.08
MIN_WEIGHT = 0.01
MAX_WEIGHT_CAP = 0.30
MIN_ENGINES_FOR_FLOOR = 6

def compute_engine_kpi(kpi_data: EngineKPI, coeffs: Dict[str, float] = DEFAULT_COEFFS) -> float:
    """
    Compute weighted KPI score.
    KPI_i = a0*overall + a10*recent10 + a20*recent20 + a30*recent30
    """
    if kpi_data.status == "STUB":
        return 0.0
        
    score = (
        coeffs['a0'] * kpi_data.overall +
        coeffs['a10'] * kpi_data.recent10 + 
        coeffs['a20'] * kpi_data.recent20 +
        coeffs['a30'] * kpi_data.recent30
    )
    return float(score)

def apply_weight_gates(
    weights: List[OmegaWeight], 
    baseline_overall: float = 0.0
) -> List[OmegaWeight]:
    """
    Apply gating logic.
    For AL1/AL2/ALX, if overall < baseline - 0.01, gate them.
    Currently, logic is minimal as per instructions, but structure is here.
    """
    return weights

def softmax_weights(
    engine_kpis: List[EngineKPI], 
    tau: float = DEFAULT_TAU
) -> List[OmegaWeight]:
    """
    Compute Softmax weights with temperature tau.
    Applies clamps (min floor, max cap).
    """
    # 1. Initialize result list aligned with input
    weights_out = []
    valid_indices = []

    for i, k in enumerate(engine_kpis):
        w = OmegaWeight(
            engine_id=k.engine_id,
            is_gated=(k.status == "STUB"),
            gate_reason="STUB" if k.status == "STUB" else None
        )
        weights_out.append(w)
        if k.status != "STUB":
            valid_indices.append(i)
    
    if not valid_indices:
        return weights_out

    # 2. Compute raw KPIs
    raw_scores = []
    
    for idx in valid_indices:
        score = compute_engine_kpi(engine_kpis[idx])
        weights_out[idx].raw_kpi = score
        raw_scores.append(score)
        
    raw_scores = np.array(raw_scores)
    
    # 3. Softmax
    # Shift by mean for stability
    mean_score = np.mean(raw_scores)
    
    # Avoid division by zero tau if somehow passed
    t_safe = tau if tau > 1e-9 else 1e-9
    
    scaled_scores = (raw_scores - mean_score) / t_safe
    exp_scores = np.exp(scaled_scores)
    sum_exp = np.sum(exp_scores)
    
    if sum_exp == 0:
        probs = np.ones_like(exp_scores) / len(exp_scores)
    else:
        probs = exp_scores / sum_exp
    
    # Assign temp weights
    for i, idx in enumerate(valid_indices):
        weights_out[idx].weight = probs[i]
        
    # 4. Apply Safety Clamps
    active_weights = np.array([weights_out[idx].weight for idx in valid_indices])
    
    if len(valid_indices) >= MIN_ENGINES_FOR_FLOOR:
        # Floor
        active_weights = np.maximum(active_weights, MIN_WEIGHT)
        # Renormalize
        sum_w = np.sum(active_weights)
        if sum_w > 0:
            active_weights = active_weights / sum_w
        
    # Cap
    if np.any(active_weights > MAX_WEIGHT_CAP):
        # Simplistic approach: clip then renormalize
        # Iterate to ensure convergence if needed, but single pass usually enough for minor adjustments
        active_weights = np.minimum(active_weights, MAX_WEIGHT_CAP)
        sum_w = np.sum(active_weights)
        if sum_w > 0:
            active_weights = active_weights / sum_w
        
    # Assign back
    for i, idx in enumerate(valid_indices):
        weights_out[idx].weight = float(active_weights[i])
        
    return weights_out

def build_candidate_pool(
    engine_topk: Dict[str, List[int]], 
    weights: List[OmegaWeight],
    k_eval: int = 20,
    k_pool: int = 22
) -> Tuple[List[int], pd.DataFrame]:
    """
    Build Candidate Pool using Weighted Borda Count / Rank Score.
    """
    # Map weights
    w_map = {w.engine_id: w.weight for w in weights if w.weight > 0}
    
    # Accumulators
    scores = {} # num -> score
    counts = {} # num -> support count
    engine_lists = {} # num -> [engine_ids]
    rank_sums = {} # num -> sum of ranks (1-based)
    
    for eid, numbers in engine_topk.items():
        if eid not in w_map:
            continue
            
        w = w_map[eid]
        
        for rank_idx, num in enumerate(numbers):
            rank = rank_idx + 1
            if rank > k_eval: 
                continue 
                
            r_score = (k_eval - rank + 1) / k_eval
            weighted_score = w * r_score
            
            scores[num] = scores.get(num, 0.0) + weighted_score
            counts[num] = counts.get(num, 0) + 1
            
            if num not in engine_lists:
                engine_lists[num] = []
            engine_lists[num].append(eid)
            
            rank_sums[num] = rank_sums.get(num, 0) + rank

    # Convert to rows
    rows = []
    all_nums = sorted(scores.keys())
    
    for n in all_nums:
        rows.append(CandidateRow(
            number=n,
            score=scores[n],
            support_count=counts[n],
            engines=engine_lists[n],
            avg_rank=rank_sums[n] / counts[n]
        ))
        
    # Sort
    # 1. Score (Desc)
    # 2. Avg Rank (Asc - Lower is better, e.g. Rank 1) -> corresponds to Higher Inverse Rank
    # 3. Number (Asc)
    rows.sort(key=lambda r: (-r.score, r.avg_rank, r.number))
    
    pool_rows = rows[:k_pool]
    pool_numbers = [r.number for r in pool_rows]
    
    # DataFrame
    df_data = []
    for r in pool_rows:
        df_data.append({
            "number": r.number,
            "score": f"{r.score:.4f}",
            "support": r.support_count,
            "avg_rank": f"{r.avg_rank:.1f}",
            "engines": ",".join(r.engines)
        })
        
    return pool_numbers, pd.DataFrame(df_data)
