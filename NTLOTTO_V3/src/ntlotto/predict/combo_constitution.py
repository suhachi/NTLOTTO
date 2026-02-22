from __future__ import annotations

def dynamic_cap(round_idx: int) -> int:
    """출현 빈도에 따른 조합 내 포함 제한 (기본 구현)"""
    return 1 # 예시: 각 번호는 최대 1번만

def generate_combo_key(nums: list[int]) -> str:
    """조합의 고유 키 (문자열) 생성"""
    return "-".join(str(n) for n in sorted(nums))

def check_overlap(combo1: list[int], combo2: list[int]) -> int:
    """두 조합 간의 겹치는 번호 개수"""
    return len(set(combo1) & set(combo2))

def is_valid_combo(combo: list[int], existing_combos: list[list[int]], max_overlap: int = 4) -> bool:
    """이전 조합들과 비교하여 유효성 검사 (너무 많이 겹치면 안됨)"""
    for ec in existing_combos:
        if check_overlap(combo, ec) > max_overlap:
            return False
    return True
