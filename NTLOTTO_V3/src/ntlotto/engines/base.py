from __future__ import annotations
import pandas as pd
from abc import ABC, abstractmethod

class EngineBase(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def score_map(self, df_s: pd.DataFrame, df_o: pd.DataFrame) -> dict[int,float]:
        """
        1부터 45까지 각 번호별 선호도/가중치를 반환
        """
        pass
