from __future__ import annotations
import math
from collections import Counter

def overlap_count(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return len(set(a) & set(b))

def jaccard(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    k = overlap_count(a, b)
    if k == 6:
        return 1.0
    return k / (12 - k)

def frequency_cap(M: int, p_max: float) -> int:
    return math.ceil(M * p_max)

def compute_new_ev_set_size(
    new_combo: tuple[int, ...], 
    selected: list[tuple[int, ...]], 
    ev_set: set[tuple[int, ...]]
) -> tuple[int, set[tuple[int, ...]]]:
    new_ev = set(ev_set)
    for c in selected:
        if overlap_count(new_combo, c) == 3:
            new_ev.add(new_combo)
            new_ev.add(c)
    return len(new_ev), new_ev

def can_add_combo(
    new_combo: tuple[int, ...], 
    selected: list[tuple[int, ...]], 
    rule_state: dict
) -> tuple[bool, str]:
    # Number Frequency Cap 검사
    for n in new_combo:
        if rule_state["counts"][n] + 1 > rule_state["cap"]:
            return False, f"Freq_cap_exceeded"

    # EV 슬롯 (조합 기준) 크기 предварительно 계산
    new_ev_size, new_ev_set = compute_new_ev_set_size(new_combo, selected, rule_state["ev_members"])
    if new_ev_size > rule_state.get("ev_slots_max", 5):
        return False, "EV_slots_full"

    # Hard Overlap & Jaccard 검사
    for ec in selected:
        k = overlap_count(new_combo, ec)
        rule_state["max_overlap_seen"] = max(rule_state["max_overlap_seen"], k)
        
        jc = jaccard(new_combo, ec)
        rule_state["max_jaccard_seen"] = max(rule_state["max_jaccard_seen"], jc)
        
        if k >= 4:
            return False, f"Hard_overlap_exceeded (k={k})"
        elif k <= 2:
            if jc > 0.30:
                return False, f"Jaccard_cap_exceeded (J={jc:.3f})"
                
    rule_state["ev_members"] = new_ev_set
    rule_state["ev_used"] = len(new_ev_set)
    return True, "OK"
