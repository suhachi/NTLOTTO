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
    pools: dict[str, dict[int, float]],
    engine_shares: dict[str, int],
    out_dir: str,
    allow_flag: bool = False
):
    if not allow_flag:
        raise RuntimeError("CLI flag --i_understand_and_allow_generation 누락.")
    _require_allow()
    ensure_dirs(out_dir)
    
    # 1) 엔진별 후보 풀(Candidate Combos Pool) 생성
    candidate_pools = []
    oversample_factor = 40
    
    # 결정론 유지
    random.seed(target_round)
    
    for eng_name, quota in engine_shares.items():
        if quota <= 0: continue
        score_map = pools.get(eng_name)
        if not score_map:
            score_map = {n: 1.0 for n in range(1, 46)}
            
        total_score = sum(score_map.values())
        if total_score <= 0:
            nums = list(range(1, 46))
            probs = [1.0/45.0]*45
        else:
            nums = list(score_map.keys())
            probs = [score_map[n]/total_score for n in nums]
            
        needed = quota * oversample_factor
        attempts = 0
        success = 0
        eng_candidates = set()
        
        while success < needed and attempts < needed * 200:
            attempts += 1
            cand_nums = set()
            inner_attempts = 0
            while len(cand_nums) < 6 and inner_attempts < 100:
                inner_attempts += 1
                pick = random.choices(nums, weights=probs, k=1)[0]
                cand_nums.add(pick)
            if len(cand_nums) == 6:
                cand = tuple(sorted(cand_nums))
                if cand not in eng_candidates:
                    eng_candidates.add(cand)
                    success += 1
                    
        for c in eng_candidates:
            c_score = sum(score_map.get(n, 0) for n in c)
            candidate_pools.append((c_score, c, eng_name))

    # 전역 선택기는 후보들을 점수 높은 순으로 정렬해 시도
    candidate_pools.sort(key=lambda x: x[0], reverse=True)
    
    # 2) 글로벌 헌법 선택기
    selected_combos = []
    selected_meta = [] # (combo: tuple, eng_name: str)
    ev_partners_log = []
    
    cap = frequency_cap(num_combos, 0.16)
    ev_slots_max = 5
    fallback_max = 5 
    
    rule_state = {
        "ev_used": 0,
        "ev_members": set(),
        "counts": Counter(),
        "cap": cap,
        "max_jaccard_seen": 0.0,
        "max_overlap_seen": 0,
        "ev_slots_max": ev_slots_max
    }

    reject_reasons = Counter()

    for score, cand, eng_name in candidate_pools:
        if cand in selected_combos:
            continue
            
        ok, reason = can_add_combo(cand, selected_combos, rule_state)
        if ok:
            for ec in selected_combos:
                if overlap_count(cand, ec) == 3:
                    ev_partners_log.append((cand, ec))
            
            selected_combos.append(cand)
            selected_meta.append((cand, eng_name))
            rule_state["counts"].update(cand)
            
            if len(selected_combos) >= num_combos:
                break
        else:
            reject_reasons[reason] += 1

    # 부족할 경우 (random fallback) - fallback_max까지만
    if len(selected_combos) < num_combos:
        needed_fallback = num_combos - len(selected_combos)
        if needed_fallback > fallback_max:
            print(f"[FAIL] 헌법 병목으로 인해 엔진 조합이 부족합니다. (필요 fallback {needed_fallback} > 최대 {fallback_max})")
            print("=== Reject Reason 카운트 ===")
            for r, c in reject_reasons.most_common():
                print(f" - {r}: {c}")
            raise RuntimeError(f"조합 선발 실패: 헌법 통과 조합 부족. Fallback 한도({fallback_max}) 초과.")
        
        attempts = 0
        while len(selected_combos) < num_combos and attempts < num_combos * 500:
            attempts += 1
            cand = tuple(sorted(random.sample(range(1, 46), 6)))
            if cand in selected_combos: continue
            
            ok, reason = can_add_combo(cand, selected_combos, rule_state)
            if ok:
                for ec in selected_combos:
                    if overlap_count(cand, ec) == 3:
                        ev_partners_log.append((cand, ec))
                    
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

    eng_actual = Counter(eng for _, eng in selected_meta)
    fallback_count = eng_actual.get("RandomFallback", 0)
    ev_combo_count = len(rule_state["ev_members"])
            
    md_lines = [
        f"# Prediction Set Round {target_round} (M={num_combos})",
        "> 이 파일은 2중 잠금 및 NTLOTTO V3 전역(Global) 헌법 통제 하에 생성된 조합입니다.",
        "",
        "## 전역 헌법 통계 (Global Selection Stats)",
        f"- Target M: {num_combos}, Generated: {len(selected_combos)}",
        f"- Max Overlap (All Pairs): {max_ov} (보장 제한: 2, 단 EV 예외는 3)",
        f"- EV Slots Used (조합 기준 ev_combo_count): {ev_combo_count} / {ev_slots_max} 최대",
        f"- EV Pair Logs Count (쌍 기준): {len(ev_partners_log)}",
        f"- Max Number Frequency: {max_cfq} / cap: {cap}",
        f"- Max Jaccard Seen: {max_jac:.3f}",
        f"- RandomFallback Count: {fallback_count} / fallback_max: {fallback_max}",
        ""
    ]
    
    md_lines.append("### Engine Actual vs Quota")
    for eng, quota in engine_shares.items():
        actual = eng_actual.get(eng, 0)
        md_lines.append(f"- {eng}: Quota {quota} -> Actual {actual}")
    md_lines.append(f"- RandomFallback: {fallback_count}")
        
    md_lines.append("\n### Reject Reason Summary (Top 5)")
    for r, c in reject_reasons.most_common(5):
        md_lines.append(f"- {r}: {c}")
        
    md_lines.append("\n### 헌법 자체 검증 (Self-Verification)")
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
