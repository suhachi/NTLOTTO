from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Literal
import pandas as pd

Round = int
Number = int
K = int
StateMode = Literal["band", "band_parity", "band_tail"]

@dataclass(frozen=True)
class SSOT:
    sorted_df: pd.DataFrame   # columns: round, date, n1..n6, bonus
    ordered_df: pd.DataFrame  # columns: round, date, b1..b6, bonus

@dataclass(frozen=True)
class FeaturePack:
    t_end: Round
    num_features: pd.DataFrame  # index=1..45, cols=freq_*, ew_freq, gap, gap_z, bonus_freq
    pair_stats: Optional[pd.DataFrame] = None # n1, n2, count, lift, pmi
    shape_stats: Optional[Dict[str, Any]] = None # band, odd_even, high_low, sum, run_len
    slot_state_probs: Optional[pd.DataFrame] = None
    markov_state: Optional[pd.DataFrame] = None

@dataclass(frozen=True)
class EngineOutput:
    engine: str
    scores: pd.DataFrame          # index=1..45, col: 'score'
    meta: Dict[str, Any]          # params, state_mode, window, etc.
    topk_diag: Dict[int, List[int]] # {15: [...], 20: [...], 25: [...]}

@dataclass(frozen=True)
class BacktestRoundResult:
    round: Round
    topk: List[Number]
    hits: int
    recall_at_k: float

@dataclass(frozen=True)
class BacktestResult:
    engine: str
    k: int
    per_round: pd.DataFrame       # columns: round, hits, recall_at_k
    mean_all: float
    mean_last10: float
    mean_last20: float
    mean_last30: float

@dataclass(frozen=True)
class OmegaInputRow:
    engine: str
    mean_all: float
    mean_last10: float
    mean_last20: float
    mean_last30: float
