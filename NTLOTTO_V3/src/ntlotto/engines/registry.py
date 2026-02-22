from __future__ import annotations

from .base import EngineBase
from .nt4 import EngineNT4
from .nt5 import EngineNT5
from .nto import EngineNTO
from .omega import EngineOmega
from .vpa1 import EngineVPA1
from .ll import EngineLL
from .pat import EnginePAT

# ✅ SSOT 고정 엔진 키 (문서/선택파일/리포트/코드 전부 동일)
ENGINE_KEYS: list[str] = [
    "NT4",
    "NT5",
    "NTO",
    "NT-Ω",
    "NT-VPA-1",
    "NT-LL",
    "NT-PAT",
]

_ENGINES_CACHE: dict[str, EngineBase] = {}

def get_engine(name: str) -> EngineBase:
    """
    SSOT 엔진 키(String)를 기반으로 Engine 인스턴스를 반환합니다.
    허용 키: NT4, NT5, NTO, NT-Ω, NT-VPA-1, NT-LL, NT-PAT
    """
    if name not in ENGINE_KEYS:
        raise KeyError(f"Unknown engine key: {name}. Allowed: {ENGINE_KEYS}")

    if name not in _ENGINES_CACHE:
        if name == "NT4":
            _ENGINES_CACHE[name] = EngineNT4()
        elif name == "NT5":
            _ENGINES_CACHE[name] = EngineNT5()
        elif name == "NTO":
            _ENGINES_CACHE[name] = EngineNTO()
        elif name == "NT-Ω":
            _ENGINES_CACHE[name] = EngineOmega()
        elif name == "NT-VPA-1":
            _ENGINES_CACHE[name] = EngineVPA1()
        elif name == "NT-LL":
            _ENGINES_CACHE[name] = EngineLL()
        elif name == "NT-PAT":
            _ENGINES_CACHE[name] = EnginePAT()
        else:
            # 이 else는 논리상 도달하지 않지만, 안전장치로 남김
            raise KeyError(f"Engine mapping missing for key: {name}")

    return _ENGINES_CACHE[name]

def default_engine_set() -> list[str]:
    """NTLOTTO v3의 기본 핵심 7 엔진 키 목록을 반환합니다."""
    return ENGINE_KEYS.copy()
