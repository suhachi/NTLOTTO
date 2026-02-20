from typing import List, Dict, Set, Optional, Any, TypedDict
from dataclasses import dataclass

@dataclass
class ScoreRow:
    round: int
    engine: str
    numbers: List[int]
    hits: int
    matched: List[int]
    bonus_hit: bool
    rank: int

class ParsedWinning(TypedDict):
    win_set: Set[int]
    bonus: int

class EngineScore(TypedDict):
    rank: int
    hits: int
    bonus_hit: bool
    score: float
    matched: List[int]
