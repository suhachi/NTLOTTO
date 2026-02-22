from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import random
import math

from ntlotto.engines.registry import get_engine, ENGINE_KEYS

Combo = Tuple[int, int, int, int, int, int]

@dataclass(frozen=True)
class CandidateCombo:
    engine: str
    nums: Combo
    score: float

def _weighted_sample_unique(nums: List[int], weights: List[float], k: int, rng: random.Random) -> List[int]:
    chosen = set()
    attempts = 0
    while len(chosen) < k:
        attempts += 1
        if attempts > 2000:
            remaining = [n for n in nums if n not in chosen]
            if len(remaining) < (k - len(chosen)):
                break
            chosen |= set(rng.sample(remaining, k - len(chosen)))
            break
        pick = rng.choices(nums, weights=weights, k=1)[0]
        chosen.add(pick)
    return sorted(chosen)

def _get_probs(score_map: Dict[int, float], power: float = 1.0) -> Tuple[List[int], List[float]]:
    xs = list(range(1, 46))
    ws = [math.pow(max(0.0001, float(score_map.get(i, 0.0))), power) for i in xs]
    s = sum(ws)
    if s <= 0:
        ws = [1.0 for _ in xs]
    return xs, ws

def build_candidate_pool_for_engine(
    engine_key: str,
    df_s,
    df_o,
    target_count: int,
    seed: int,
) -> List[CandidateCombo]:
    rng = random.Random(seed + (hash(engine_key) & 0xFFFF))
    eng = get_engine(engine_key)
    score_map = eng.score_map(df_s, df_o) 

    pool: List[CandidateCombo] = []
    seen = set()

    # 분산 전략 보완 (통과 확률 극대화): 
    # 20%: Original Weights (Hard)
    # 30%: Sqrt Weights (Soft)
    # 50%: Uniform Weights (Flexible)
    strategies = [
        (1.0, int(target_count * 0.2)),
        (0.5, int(target_count * 0.3)),
        (0.0, target_count - int(target_count * 0.2) - int(target_count * 0.3))
    ]

    for power, count in strategies:
        nums, weights = _get_probs(score_map, power)
        added = 0
        tries = 0
        while added < count and tries < count * 100:
            tries += 1
            pick6 = _weighted_sample_unique(nums, weights, 6, rng)
            if len(pick6) != 6:
                continue
            combo = tuple(pick6)
            if combo in seen:
                continue
            seen.add(combo)
            # score is always original sum
            sc = sum(float(score_map.get(n, 0.0)) for n in combo)
            pool.append(CandidateCombo(engine=engine_key, nums=combo, score=sc))
            added += 1

    pool.sort(key=lambda c: (-c.score, c.nums))
    return pool

def build_all_candidate_pools(
    df_s,
    df_o,
    quotas: Dict[str, int],
    oversample_factor: int,
    seed: int,
) -> Dict[str, List[CandidateCombo]]:
    pools: Dict[str, List[CandidateCombo]] = {}
    for eng, q in quotas.items():
        if q <= 0:
            pools[eng] = []
            continue
        target = max(q * oversample_factor, q * 20)
        pools[eng] = build_candidate_pool_for_engine(eng, df_s, df_o, target, seed)
    return pools
