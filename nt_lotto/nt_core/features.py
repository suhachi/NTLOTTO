from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List, Any
from .schema import SSOT, FeaturePack, StateMode
from .constants import WINDOWS_DEFAULT, EW_ALPHA_DEFAULT, PAIR_WINDOW_DEFAULT

BANDS = [(1,9),(10,19),(20,29),(30,39),(40,45)]

def band_of(n: int) -> int:
    for i,(a,b) in enumerate(BANDS, start=1):
        if a <= n <= b:
            return i
    raise ValueError(n)

def build_feature_pack(ssot: SSOT, t_end: int, windows=WINDOWS_DEFAULT, ew_alpha=EW_ALPHA_DEFAULT, ew_k=200, use_state: StateMode = "band_parity", pair_window=PAIR_WINDOW_DEFAULT) -> FeaturePack:
    sorted_df = ssot.sorted_df[ssot.sorted_df["round"] <= t_end].copy()
    ordered_df = ssot.ordered_df[ssot.ordered_df["round"] <= t_end].copy()
    
    num_feats = _number_features(sorted_df, windows, ew_alpha, ew_k)
    pair_stats = _pair_features_v2(sorted_df, window=pair_window)
    shape_stats = _shape_features(sorted_df)
    
    slot_probs, markov = _order_features(ordered_df, windows, use_state)
    
    return FeaturePack(
        t_end=t_end,
        num_features=num_feats,
        pair_stats=pair_stats,
        shape_stats=shape_stats,
        slot_state_probs=slot_probs,
        markov_state=markov
    )

def _number_features(sorted_df: pd.DataFrame, windows, ew_alpha, ew_k) -> pd.DataFrame:
    if sorted_df.empty:
        return pd.DataFrame(index=range(1,46))
    rounds = sorted_df["round"].tolist()
    wins = sorted_df[["n1","n2","n3","n4","n5","n6"]].values.tolist()
    bonuses = sorted_df["bonus"].tolist()
    idx = np.arange(1, 46)
    feats = {}
    for W in windows:
        feats[f"freq_{W}"] = _freq_window(idx, wins, W)
    feats["ew_freq"] = _freq_ew(idx, wins, alpha=ew_alpha, k=ew_k)
    last_seen = _last_seen(idx, rounds, wins)
    t_now = max(rounds) if rounds else 0
    gap = np.where(last_seen > 0, t_now - last_seen, t_now) 
    feats["gap"] = gap
    feats["gap_z"] = _zscore(gap)
    feats["bonus_freq_50"] = _bonus_freq_window(idx, bonuses, W=50)
    df = pd.DataFrame(feats, index=idx)
    return df

def _pair_features_v2(sorted_df: pd.DataFrame, window: int) -> pd.DataFrame:
    recent_df = sorted_df.tail(window)
    if recent_df.empty: return pd.DataFrame()
    
    from itertools import combinations
    pair_counts = {}
    indiv_counts = {}
    N = len(recent_df)
    
    wins = recent_df[["n1","n2","n3","n4","n5","n6"]].values
    for row in wins:
        for n in row:
            indiv_counts[n] = indiv_counts.get(n, 0) + 1
        for p in combinations(sorted(row), 2):
            pair_counts[p] = pair_counts.get(p, 0) + 1
            
    rows = []
    for (n1, n2), c_pair in pair_counts.items():
        p_n1 = indiv_counts[n1] / N
        p_n2 = indiv_counts[n2] / N
        p_pair = c_pair / N
        
        lift = p_pair / (p_n1 * p_n2) if (p_n1 * p_n2) > 0 else 0
        try:
            pmi = np.log2(p_pair / (p_n1 * p_n2)) if p_pair > 0 else -10.0
        except:
            pmi = -10.0
        
        rows.append({'n1': n1, 'n2': n2, 'count': c_pair, 'lift': lift, 'pmi': pmi})
        
    return pd.DataFrame(rows)

def _shape_features(sorted_df: pd.DataFrame) -> Dict[str, Any]:
    if sorted_df.empty: return {}
    wins = sorted_df[["n1","n2","n3","n4","n5","n6"]].values
    
    sums = np.sum(wins, axis=1)
    odds = np.sum(wins % 2 != 0, axis=1)
    highs = np.sum(wins >= 23, axis=1) 
    
    df = pd.DataFrame({
        'round': sorted_df['round'],
        'sum': sums,
        'odd_count': odds,
        'high_count': highs
    })
    
    stats = {
        'sum_stats': df['sum'].describe().to_dict(),
        'pattern_counts': df[['odd_count', 'high_count']].value_counts(normalize=True).to_frame(name='prob').reset_index().to_dict('records')
    }
    return stats

def _order_features(ordered_df: pd.DataFrame, windows, use_state: StateMode):
    if ordered_df.empty: return None, None
    bcols = ["b1","b2","b3","b4","b5","b6"]
    arr = ordered_df[bcols].values
    states = np.vectorize(lambda n: _state(n, use_state))(arr)
    slot_probs = _slot_state_probs(states)
    markov = _markov_transition(states)
    return slot_probs, markov

def _state(n: int, use_state: StateMode):
    b = band_of(n)
    if use_state == "band": return f"B{b}"
    if use_state == "band_parity": return f"B{b}_{'O' if n%2 else 'E'}"
    if use_state == "band_tail": 
        tail = n % 10
        return f"B{b}_T{tail}"
    return f"B{b}"

def _slot_state_probs(states: np.ndarray) -> pd.DataFrame:
    slots = {}
    for j in range(6):
        col = states[:, j]
        vc = pd.Series(col).value_counts(normalize=True)
        slots[f"slot{j+1}"] = vc
    return pd.DataFrame(slots).fillna(0.0)

def _markov_transition(states: np.ndarray) -> pd.DataFrame:
    pairs = []
    for row in range(len(states)):
        for j in range(5):
            pairs.append((states[row, j], states[row, j+1]))
    if not pairs: return pd.DataFrame()
    s = pd.Series(pairs)
    counts = s.value_counts()
    from_counts = {}
    for (a,b), c in counts.items():
        from_counts[a] = from_counts.get(a, 0) + c
    rows = []
    for (a,b), c in counts.items():
        p = c / from_counts[a]
        rows.append((a,b,p,c))
    return pd.DataFrame(rows, columns=["from","to","p","count"])

def _freq_window(idx, wins, W: int) -> np.ndarray:
    recent = wins[-W:] if len(wins) >= W else wins
    denom = max(1, len(recent))
    counts = np.zeros(45, dtype=float)
    for row in recent:
        for n in row: counts[n-1] += 1.0
    return counts / denom

def _freq_ew(idx, wins, alpha=0.93, k=200) -> np.ndarray:
    recent = wins[-k:] if len(wins) >= k else wins
    weights = np.array([alpha**i for i in range(len(recent))][::-1], dtype=float)
    weights = weights / weights.sum() if weights.sum() > 0 else weights
    counts = np.zeros(45, dtype=float)
    for w, row in zip(weights, recent):
        for n in row: counts[n-1] += w
    return counts

def _last_seen(idx, rounds, wins) -> np.ndarray:
    last = np.zeros(45, dtype=int)
    for r, row in zip(rounds, wins):
        for n in row:
            if n > 0 and n <= 45: last[n-1] = r
    return last

def _bonus_freq_window(idx, bonuses, W=50) -> np.ndarray:
    recent = bonuses[-W:] if len(bonuses) >= W else bonuses
    denom = max(1, len(recent))
    counts = np.zeros(45, dtype=float)
    for b in recent:
        if b > 0 and b <= 45: counts[b-1] += 1.0
    return counts / denom

def _zscore(x: np.ndarray) -> np.ndarray:
    x = x.astype(float)
    m = np.nanmean(x)
    s = np.nanstd(x)
    if s == 0 or np.isnan(s): return np.zeros_like(x)
    return (x - m) / s
