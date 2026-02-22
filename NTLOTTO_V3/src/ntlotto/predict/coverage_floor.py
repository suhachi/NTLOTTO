from __future__ import annotations
import random

def enforce_coverage_floor(
    combos: list[list[int]],
    required_numbers: list[int],
    target_count: int
) -> list[list[int]]:
    """
    모든 required_numbers가 최소 1회 이상은 조합들에 포함되도록 보장.
    만약 누락된 번호가 있다면 마지막 번호들을 강제로 교체.
    """
    if not combos:
        return combos
        
    used = set()
    for c in combos:
        used.update(c)
        
    missing = [x for x in required_numbers if x not in used]
    if not missing:
        return combos
        
    # 누락된 번호를 뒤쪽 조합부터 강제로 찔러넣음 (간단한 구현)
    mutated = [list(c) for c in combos]
    idx = len(mutated) - 1
    
    for m in missing:
        if idx < 0:
            idx = len(mutated) - 1
        
        # 교체할 슬롯 선택 (임의)
        slot = random.randint(0, 5)
        mutated[idx][slot] = m
        mutated[idx] = sorted(list(set(mutated[idx])))
        
        # 만약 길이가 6이 안되면(우연히 겹친 경우) 다른 안쓰인 번호 추가
        while len(mutated[idx]) < 6:
            r = random.randint(1, 45)
            if r not in mutated[idx]:
                mutated[idx].append(r)
        mutated[idx].sort()
        idx -= 1
        
    return mutated
