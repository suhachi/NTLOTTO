from __future__ import annotations
import os, json, random
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from ntlotto.core.report_writer import write_text
from ntlotto.contracts.engine_contract import assert_engine_keys_map
from ntlotto.contracts.constitution_contract import assert_constitution
from ntlotto.predict.constitution import (
    overlap_count,
    compute_new_ev_set_size,
)
from ntlotto.predict.candidate_pools import build_all_candidate_pools, CandidateCombo

Combo = Tuple[int,int,int,int,int,int]

@dataclass
class RuleState:
    M: int
    cap: int
    p_max: float
    ev_slots_max: int
    fallback_max: int
    counts: Counter
    ev_set: set
    selected: List[Tuple[str, Combo]]  # (engine, combo)
    reject_reasons_global: Counter
    reject_reasons_by_engine: Dict[str, Counter]

def _require_allow() -> None:
    if os.environ.get("ALLOW_COMBO_GENERATION") != "1":
        raise RuntimeError("조합 생성은 기본 OFF입니다. ALLOW_COMBO_GENERATION=1 설정 후에만 실행 가능합니다.")

def _freq_cap(M: int, p_max: float) -> int:
    import math
    return int(math.ceil(M * p_max))

def _would_violate_freq(counts: Counter, combo: Combo, cap: int) -> bool:
    tmp = counts.copy()
    tmp.update(combo)
    return (max(tmp.values()) if tmp else 0) > cap

def _can_add_combo(
    st: RuleState,
    engine: str,
    combo: Combo,
) -> Tuple[bool, str, Optional[set]]:
    # HARD: overlap >=4 금지
    for _, ex in st.selected:
        ov = overlap_count(combo, ex)
        if ov >= 4:
            return False, "Hard_overlap_exceeded (k>=4)", None

    # overlap==3 -> EV 슬롯(조합 기준) 검사
    new_ev_set = None
    for _, ex in st.selected:
        if overlap_count(combo, ex) == 3:
            new_size, new_ev = compute_new_ev_set_size(combo, [c for _,c in st.selected], st.ev_set)
            if new_size > st.ev_slots_max:
                return False, "EV_slots_full", None
            new_ev_set = new_ev  # 업데이트 예정

    # Frequency cap
    if _would_violate_freq(st.counts, combo, st.cap):
        return False, "Freq_cap_exceeded", None

    return True, "OK", new_ev_set

def _record_reject(st: RuleState, engine: str, reason: str) -> None:
    st.reject_reasons_global[reason] += 1
    st.reject_reasons_by_engine[engine][reason] += 1

def generate_from_selection(
    selection_path: str,
    out_md: str,
    out_csv: str,
) -> dict:
    _require_allow()

    sel = json.loads(Path(selection_path).read_text(encoding="utf-8"))
    R = int(sel.get("round"))
    M = int(sel.get("M", 50))
    seed = int(sel.get("seed", 0))

    constitution = sel.get("constitution", {})
    p_max = float(constitution.get("p_max", 0.20))
    ev_slots_max = int(constitution.get("ev_slots_max", 5))
    fallback_max = int(constitution.get("fallback_max", 5))
    oversample_factor = int(constitution.get("oversample_factor", 1000))

    engines_cfg = sel.get("engines", sel.get("engine_selection", {}))
    quotas: Dict[str, int] = {}
    for k,v in engines_cfg.items():
        if v.get("enabled", v.get("use", False)) and int(v.get("quota", 0)) > 0:
            quotas[k] = int(v["quota"])

    # Contract Verification (FAIL-FAST)
    assert_constitution(constitution)
    assert_engine_keys_map({k:1 for k in quotas.keys()})

    # LOAD SSOT
    ssot_sorted_path = sel.get("ssot_sorted_path", "data/ssot_sorted.csv")
    ssot_ordered_path = ssot_sorted_path.replace("sorted", "ordered")
    
    from ntlotto.core.load_ssot import load_ssot
    df_s, df_o = load_ssot(ssot_sorted_path, ssot_ordered_path)
    
    # Filter by round
    df_s = df_s[df_s["round"] < R]
    df_o = df_o[df_o["round"] < R]

    cap = _freq_cap(M, p_max)

    st = RuleState(
        M=M, cap=cap, p_max=p_max, ev_slots_max=ev_slots_max, fallback_max=fallback_max,
        counts=Counter(), ev_set=set(), selected=[],
        reject_reasons_global=Counter(),
        reject_reasons_by_engine=defaultdict(Counter),
    )

    # 1) 엔진별 후보풀 분리 생성
    pools = build_all_candidate_pools(df_s, df_o, quotas, oversample_factor, seed)

    # 2) Quota Enforced Fill (엔진별로 quota만큼 반드시 채움)
    # 엔진 순서를 셔플하여 순서에 따른 빈도 제한 불이익 방지
    eng_keys = list(quotas.keys())
    rng_global = random.Random(seed)
    rng_global.shuffle(eng_keys)

    for eng in eng_keys:
        q = quotas[eng]
        need = q
        # 후보군 점수에 약간의 jitter를 섞어 정렬 (인기 번호만 쏠리는 현상 방지)
        pool = pools.get(eng, [])
        pool_with_jitter = []
        for cand in pool:
            jitter = rng_global.random() * 0.5
            pool_with_jitter.append((cand.score + jitter, cand))
        pool_with_jitter.sort(key=lambda x: -x[0])
        
        added = 0
        for _, cand in pool_with_jitter:
            if added >= need:
                break
            ok, reason, new_ev = _can_add_combo(st, eng, cand.nums)
            if not ok:
                _record_reject(st, eng, reason)
                continue
            # accept
            st.selected.append((eng, cand.nums))
            st.counts.update(cand.nums)
            if new_ev is not None:
                st.ev_set = new_ev
            added += 1

        if added < need:
            raise RuntimeError(
                f"[QUOTA_FAIL] Engine {eng} quota not met: need={need}, got={added}. "
                f"TopRejects={st.reject_reasons_by_engine[eng].most_common(5)}"
            )

    # 3) fallback fill
    fallback_used = 0
    if len(st.selected) < M:
        merged: List[CandidateCombo] = []
        for eng, pool in pools.items():
            merged.extend(pool[: max(50, quotas.get(eng, 0)*5)])
        merged.sort(key=lambda c: (-c.score, c.nums))

        for cand in merged:
            if len(st.selected) >= M:
                break
            ok, reason, new_ev = _can_add_combo(st, "RandomFallback", cand.nums)
            if not ok:
                _record_reject(st, "RandomFallback", reason)
                continue
            st.selected.append(("RandomFallback", cand.nums))
            st.counts.update(cand.nums)
            if new_ev is not None:
                st.ev_set = new_ev
            fallback_used += 1
            if fallback_used > fallback_max:
                raise RuntimeError(f"[FALLBACK_FAIL] fallback_used exceeded: {fallback_used} > {fallback_max}")

    if len(st.selected) != M:
        raise RuntimeError(f"[M_FAIL] Expected M={M}, got={len(st.selected)}")

    # 4) compute stats
    combos_only = [c for _,c in st.selected]
    max_overlap = 0
    ov4 = 0
    ev_combo_set = set()
    ev_pair_logs = []
    for i in range(M):
        for j in range(i+1, M):
            ov = overlap_count(combos_only[i], combos_only[j])
            if ov > max_overlap:
                max_overlap = ov
            if ov >= 4:
                ov4 += 1
            if ov == 3:
                ev_combo_set.add(combos_only[i]); ev_combo_set.add(combos_only[j])
                ev_pair_logs.append((combos_only[i], combos_only[j]))

    max_freq = max(st.counts.values()) if st.counts else 0

    # 5) write outputs
    csv_lines = ["round,engine,n1,n2,n3,n4,n5,n6"]
    for idx, (eng, combo) in enumerate(st.selected, start=1):
        csv_lines.append(f"{R},{eng}," + ",".join(map(str, combo)))
    Path(out_csv).write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    eng_counts = Counter([e for e,_ in st.selected])
    md = []
    md.append(f"# Prediction Set Round {R} (M={M})")
    md.append("> 이 파일은 2중 잠금 및 NTLOTTO V3 전역(Global) 헌법 통제 하에 생성된 조합입니다.")
    md.append("")
    md.append("## 전역 헌법 통계 (Global Selection Stats)")
    md.append(f"- Target M: {M}, Generated: {M}")
    md.append(f"- Max Overlap (All Pairs): {max_overlap} (보장 제한: 2, 단 EV 예외는 3)")
    md.append(f"- EV Slots Used (조합 기준 ev_combo_count): {len(ev_combo_set)} / {ev_slots_max} 최대")
    md.append(f"- EV Pair Logs Count (쌍 기준): {len(ev_pair_logs)}")
    md.append(f"- Max Number Frequency: {max_freq} / cap: {cap}")
    md.append(f"- RandomFallback Count: {eng_counts.get('RandomFallback',0)} / fallback_max: {fallback_max}")
    md.append("")
    md.append("### Engine Actual vs Quota")
    for eng, q in quotas.items():
        md.append(f"- {eng}: Quota {q} -> Actual {eng_counts.get(eng,0)}")
    md.append(f"- RandomFallback: {eng_counts.get('RandomFallback',0)}")
    md.append("")
    md.append("### Reject Reason Summary (Top 5)")
    for k,v in st.reject_reasons_global.most_common(5):
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("### 헌법 자체 검증 (Self-Verification)")
    md.append(f"- Overlap >= 4 존재여부: {'PASS 기록 (0건)' if ov4==0 else f'FAIL (count={ov4})'}")
    md.append(f"- Frequency 초과 위반: {'PASS 기록 (0건)' if max_freq<=cap else f'FAIL (max_freq={max_freq} > cap={cap})'}")
    md.append(f"- EV 슬롯(조합 기준) 위반: {'PASS 기록' if len(ev_combo_set)<=ev_slots_max else 'FAIL'}")
    md.append(f"- 전역 헌법 무결성: {'PASS' if (ov4==0 and max_freq<=cap and len(ev_combo_set)<=ev_slots_max and eng_counts.get('RandomFallback',0)<=fallback_max) else 'FAIL'}")
    md.append("")
    md.append("## EV 슬롯(공유 3) 허용 내역 로그")
    for a,b in ev_pair_logs[:50]:
        md.append(f"- {list(a)} <-> {list(b)}")
    md.append("")
    md.append("## 조합 목록")
    for idx, (eng, combo) in enumerate(st.selected, start=1):
        md.append(f"{idx:02d}. [{', '.join(map(str, combo))}] ({eng})")

    Path(out_md).write_text("\n".join(md) + "\n", encoding="utf-8")

    return {
        "round": R,
        "M": M,
        "max_overlap": max_overlap,
        "ov4_count": ov4,
        "ev_combo_count": len(ev_combo_set),
        "max_freq": max_freq,
        "cap": cap,
        "fallback_count": eng_counts.get("RandomFallback",0),
        "engine_actual": dict(eng_counts),
        "reject_top": st.reject_reasons_global.most_common(10),
    }
