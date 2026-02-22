from __future__ import annotations
import math
from collections import Counter

def overlap_count(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    """두 조합의 공통 원소 개수 반환"""
    return len(set(a) & set(b))

def jaccard(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    """자카드 유사도 산출 (k / (12-k))"""
    k = overlap_count(a, b)
    if k == 6:
        return 1.0
    return k / (12 - k)

def frequency_cap(M: int, p_max: float) -> int:
    """전체 생성 갯수(M) 대비 개별 번호 출현 상한선 계산"""
    return math.ceil(M * p_max)

def can_add_combo(
    new_combo: tuple[int, ...], 
    selected: list[tuple[int, ...]], 
    rule_state: dict
) -> tuple[bool, str]:
    """
    rule_state 예상 딕셔너리 포맷:
    {
        "ev_used": int (현 사용량),
        "ev_members": set[tuple],
        "counts": Counter,
        "cap": int,
        "max_jaccard_seen": float,
        "max_overlap_seen": int
    }
    """
    # 2. Number Frequency Cap 검사 (어떤 번호도 cap 초과 불가)
    for n in new_combo:
        if rule_state["counts"][n] + 1 > rule_state["cap"]:
            return False, f"Freq_cap_exceeded"

    # 1. Hard Overlap & EV & Jaccard 검사
    is_ev_needed = False
    
    for ec in selected:
        k = overlap_count(new_combo, ec)
        rule_state["max_overlap_seen"] = max(rule_state["max_overlap_seen"], k)
        
        jc = jaccard(new_combo, ec)
        rule_state["max_jaccard_seen"] = max(rule_state["max_jaccard_seen"], jc)
        
        if k >= 4:
            return False, f"Hard_overlap_exceeded (k={k})"
        elif k == 3:
            is_ev_needed = True
        else:
            # k <= 2, jaccard 기본 체크
            if jc > 0.30:
                return False, f"Jaccard_cap_exceeded (J={jc:.3f})"
                
    if is_ev_needed:
        if rule_state["ev_used"] >= 5:
            return False, "EV_slots_full"

    return True, "OK"
