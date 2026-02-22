from __future__ import annotations
import os
import random
import csv
from collections import Counter
import pandas as pd

from ..core.report_writer import ensure_dirs, write_text
from .constitution import overlap_count, jaccard, frequency_cap, can_add_combo

def _require_allow():
    val = os.environ.get("ALLOW_COMBO_GENERATION", "0")
    if val != "1":
        raise RuntimeError("조합 생성이 잠겨있습니다. ALLOW_COMBO_GENERATION=1 필요.")

def generate_predictions(
    target_round: int,
    num_combos: int,
    pools: dict[str, list[int]],
    engine_shares: dict[str, int],
    out_dir: str,
    allow_flag: bool = False
):
    if not allow_flag:
        raise RuntimeError("CLI flag --i_understand_and_allow_generation 누락.")
    _require_allow()
    ensure_dirs(out_dir)
    
    # 1) 엔진별 후보 풀(Candidate Combos Pool) 생성 (넉넉히 quota의 6배)
    candidate_pools = []
    
    for eng_name, quota in engine_shares.items():
        if quota <= 0: continue
        pool = pools.get(eng_name, list(range(1, 46)))
        needed = quota * 6
        attempts = 0
        success = 0
        eng_candidates = set()
        
        while success < needed and attempts < needed * 50:
            attempts += 1
            if len(pool) < 6:
                cand = tuple(sorted(random.sample(range(1, 46), 6)))
            else:
                cand = tuple(sorted(random.sample(pool, 6)))
                
            if cand not in eng_candidates:
                eng_candidates.add(cand)
                success += 1
        
        for c in eng_candidates:
            candidate_pools.append((c, eng_name))

    # 엔진 편향 방지를 위해 섞기 (실제론 점수 높은 순 정렬 방식을 쓸 수도 있으나, 여기선 랜덤 셔플)
    random.shuffle(candidate_pools)
    
    # 2) 글로벌 헌법 선택기
    selected_combos = []
    selected_meta = [] # (combo: tuple, eng_name: str)
    ev_partners_log = []
    
    cap = frequency_cap(num_combos, 0.16)
    rule_state = {
        "ev_used": 0,
        "ev_members": set(),
        "counts": Counter(),
        "cap": cap,
        "max_jaccard_seen": 0.0,
        "max_overlap_seen": 0
    }

    reject_reasons = Counter()

    for cand, eng_name in candidate_pools:
        if cand in selected_combos:
            continue
            
        ok, reason = can_add_combo(cand, selected_combos, rule_state)
        if ok:
            is_ev = False
            for ec in selected_combos:
                if overlap_count(cand, ec) == 3:
                    is_ev = True
                    rule_state["ev_members"].add(cand)
                    rule_state["ev_members"].add(ec)
                    ev_partners_log.append((cand, ec))
            if is_ev:
                rule_state["ev_used"] += 1
                
            selected_combos.append(cand)
            selected_meta.append((cand, eng_name))
            rule_state["counts"].update(cand)
            
            if len(selected_combos) >= num_combos:
                break
        else:
            reject_reasons[reason] += 1

    # 부족할 경우 (random fallback)
    attempts = 0
    while len(selected_combos) < num_combos and attempts < num_combos * 500:
        attempts += 1
        cand = tuple(sorted(random.sample(range(1, 46), 6)))
        if cand in selected_combos: continue
        
        ok, reason = can_add_combo(cand, selected_combos, rule_state)
        if ok:
            is_ev = False
            for ec in selected_combos:
                if overlap_count(cand, ec) == 3:
                    is_ev = True
                    rule_state["ev_members"].add(cand)
                    rule_state["ev_members"].add(ec)
                    ev_partners_log.append((cand, ec))
            if is_ev:
                rule_state["ev_used"] += 1
                
            selected_combos.append(cand)
            selected_meta.append((cand, "RandomFallback"))
            rule_state["counts"].update(cand)

    # 결과 검증 및 통계 산출
    max_ov = 0
    max_jac = 0.0
    v_overlap_4 = 0
    v_freq_viol = 0
    
    for i in range(len(selected_combos)):
        for j in range(i+1, len(selected_combos)):
            ov = overlap_count(selected_combos[i], selected_combos[j])
            max_ov = max(max_ov, ov)
            jc = jaccard(selected_combos[i], selected_combos[j])
            max_jac = max(max_jac, jc)
            if ov >= 4:
                v_overlap_4 += 1
                
    for v in rule_state["counts"].values():
        if v > cap:
            v_freq_viol += 1
            
    max_cfq = max(rule_state["counts"].values()) if rule_state["counts"] else 0
    
    csv_path = f"{out_dir}/NTUC_{target_round}_combos.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["round","n1","n2","n3","n4","n5","n6"])
        for c, _ in selected_meta:
            w.writerow([target_round] + list(c))
            
    md_lines = [
        f"# Prediction Set Round {target_round} (M={num_combos})",
        "> 이 파일은 2중 잠금 및 NTLOTTO V3 전역(Global) 헌법 통제 하에 생성된 조합입니다.",
        "",
        "## 전역 헌법 통계 (Global Selection Stats)",
        f"- Target M: {num_combos}, Generated: {len(selected_combos)}",
        f"- Max Overlap (All Pairs): {max_ov} (보장 제한: 2, 단 EV 예외는 3)",
        f"- EV Slots Used (Overlap=3): {rule_state['ev_used']} / 5 최대",
        f"- Max Number Frequency: {max_cfq} (Frequency Cap: {cap})",
        f"- Max Jaccard Seen: {max_jac:.3f}",
        ""
    ]
    
    md_lines.append("### 헌법 자체 검증 (Self-Verification)")
    md_lines.append(f"- Overlap >= 4 존재여부: {'PASS 기록 (0건)' if v_overlap_4 == 0 else f'FAIL ({v_overlap_4}건 발생)'}")
    md_lines.append(f"- Frequency 초과 위반: {'PASS 기록 (0건)' if v_freq_viol == 0 else f'FAIL ({v_freq_viol}건 발생)'}")
    if v_overlap_4 == 0 and v_freq_viol == 0 and len(selected_combos) == num_combos:
        md_lines.append("- 전역 헌법 무결성: PASS")
    else:
        md_lines.append("- 전역 헌법 무결성: FAIL 적발됨")
        
    md_lines.append("")
    md_lines.append("## EV 슬롯(공유 3) 허용 내역 로그")
    if not ev_partners_log:
        md_lines.append("- 허용된 내역 없음")
    else:
        for a, b in ev_partners_log:
            md_lines.append(f"- {list(a)} <-> {list(b)}")
            
    md_lines.append("")
    md_lines.append("## 조합 목록")
    for i, (c, eng) in enumerate(selected_meta, 1):
        md_lines.append(f"{i:02d}. {list(c)} ({eng})")
        
    write_text(f"{out_dir}/Prediction_Set_R{target_round}_M{num_combos}.md", "\n".join(md_lines))
    print(f"[*] 글로벌 조합 M={len(selected_combos)} 생성 통과. (Saved to {out_dir})")
