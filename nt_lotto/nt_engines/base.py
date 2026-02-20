from typing import List, Protocol, Optional, Set
import pandas as pd

class EngineBase(Protocol):
    """
    Protocol for NT Lotto Engines.
    Strictly for Top-K generation, no full combination generation.
    """
    engine_id: str
    required_ssot: str # "sorted", "ordered", "both"
    
    def fit(self, train_sorted: pd.DataFrame, train_ordered: Optional[pd.DataFrame]) -> None:
        """
        Train the engine on historical data.
        """
        ...
        
    def topk_numbers(self, k: int) -> List[int]:
        """
        Return top K candidate numbers for the next round.
        """
        ...

class StubEngine:
    """
    Placeholder for engines not yet implemented.
    Returns empty list for topk.
    """
    def __init__(self, engine_id: str, required_ssot: str = "sorted"):
        self.engine_id = engine_id
        self.required_ssot = required_ssot
        self.fitted = False
        
    def fit(self, train_sorted: pd.DataFrame, train_ordered: Optional[pd.DataFrame]) -> None:
        self.fitted = True
        
    def topk_numbers(self, k: int) -> List[int]:
        # Return empty list to indicate no prediction
        return []
