from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class EngineKPI:
    engine_id: str
    status: str
    overall: float
    recent10: float
    recent20: float
    recent30: float
    n_eval_rounds: int

@dataclass
class OmegaWeight:
    engine_id: str
    raw_kpi: float = 0.0
    weight: float = 0.0
    is_gated: bool = False
    gate_reason: Optional[str] = None

@dataclass
class CandidateRow:
    number: int
    score: float
    support_count: int
    engines: List[str]
    avg_rank: float

@dataclass
class ComboCandidate:
    engine_id: str
    numbers: List[int]
    score: float
    meta: Dict = field(default_factory=dict)

@dataclass
class QARules:
    max_overlap: int = 2
    max_freq: int = 8
    max_jaccard: float = 0.30

@dataclass
class QAReport:
    overlap_violations: int
    freq_violations: int
    jaccard_violations: int
    portfolio_size: int
    hard_pass: bool
    soft_pass: bool
    details: Dict = field(default_factory=dict)

