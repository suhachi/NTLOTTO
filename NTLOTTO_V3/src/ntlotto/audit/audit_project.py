import argparse
import os
import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter
from ntlotto.core.load_ssot import load_ssot
from ntlotto.core.validate_ssot import validate_ssot
from ntlotto.predict.constitution import overlap_count, jaccard

def parse_combos_from_md(lines):
    combos = []
    engines = []
    in_combo_section = False
    for line in lines:
        if line.startswith("## 조합 목록"):
            in_combo_section = True
            continue
        if in_combo_section:
            m = re.match(r"^\d+\.\s+\[(.*?)\]\s+\((.*?)\)", line)
            if m:
                nums_str = m.group(1)
                eng = m.group(2)
                nums = tuple(sorted(int(x.strip()) for x in nums_str.split(",")))
                combos.append(nums)
                engines.append(eng)
    return combos, engines

def parse_md_stats(lines):
    stats = {}
    for line in lines:
        m_overlap = re.search(r"Max Overlap \(All Pairs\):\s+(\d+)", line)
        if m_overlap: stats["max_overlap"] = int(m_overlap.group(1))
        
        m_ev = re.search(r"EV Slots Used \(Overlap=3\):\s+(\d+)", line)
        if m_ev: stats["ev_slots_used"] = int(m_ev.group(1))
        
        m_freq = re.search(r"Max Number Frequency:\s+(\d+)", line)
        if m_freq: stats["max_freq"] = int(m_freq.group(1))

        m_jac = re.search(r"Max Jaccard Seen:\s+([0-9.]+)", line)
        if m_jac: stats["max_jaccard"] = float(m_jac.group(1))
        
        if "Overlap >= 4 존재여부:" in line:
            stats["overlap_4_pass"] = "PASS 기록" in line
        if "Frequency 초과 위반:" in line:
            stats["freq_viol_pass"] = "PASS 기록" in line
    return stats

def run_audit(target_round, M, p_max, ev_slots_max, fallback_max):
    base_dir = Path("c:/Users/a/OneDrive/바탕 화면/로또분석/NTLOTTO_V3")
    latest_dir = base_dir / "docs/reports/latest"
    ssot_sorted = base_dir / "data/ssot_sorted.csv"
    ssot_ordered = base_dir / "data/ssot_ordered.csv"
    
    audit_results = {
        "conclusion": "FAIL",
        "timestamp": datetime.now().isoformat(),
        "round": target_round,
        "metrics": {},
        "checks": []
    }
    
    # 2-A) SSOT 
    print("[*] 2-A SSOT Verification...")
    try:
        df_s, df_o = load_ssot(str(ssot_sorted), str(ssot_ordered))
        val_res = validate_ssot(df_s, df_o)
        audit_results["checks"].append({"id": "SSOT_INTEGRITY", "status": "PASS", "reason": f"Rows={val_res['rows']}"})
    except Exception as e:
        audit_results["checks"].append({"id": "SSOT_INTEGRITY", "status": "FAIL", "reason": str(e)})

    # 2-B) Layer separation
    print("[*] 2-B Layer Separation Verification...")
    report_files = list(latest_dir.glob("*.md"))
    has_prediction = any(f.name.startswith("Prediction_Set") for f in report_files)
    
    # 2-C) Prediction result validation
    print("[*] 2-C Prediction Result Validation...")
    md_path = latest_dir / f"Prediction_Set_R{target_round}_M{M}.md"
    if not md_path.exists():
        audit_results["checks"].append({"id": "PREDICT_OUTPUT", "status": "FAIL", "reason": "Prediction_Set MD not found"})
        with open(latest_dir / f"AUDIT_R{target_round}_M{M}.json", "w", encoding='utf-8') as f:
            json.dump(audit_results, f, ensure_ascii=False, indent=2)
        return
        
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        lines = md_text.splitlines()
        
    md_stats = parse_md_stats(lines)
    combos, engines_list = parse_combos_from_md(lines)
    
    if len(combos) != M:
        audit_results["checks"].append({"id": "M_TARGET", "status": "FAIL", "reason": f"Expected M={M}, got {len(combos)}"})
    else:
        audit_results["checks"].append({"id": "M_TARGET", "status": "PASS", "reason": f"Generated={M}"})
    
    # Recalculate
    actual_max_overlap = 0
    actual_ov_4_count = 0
    ev_combo_set = set()
    actual_max_jac = 0.0
    
    for i in range(len(combos)):
        for j in range(i+1, len(combos)):
            ov = overlap_count(combos[i], combos[j])
            actual_max_overlap = max(actual_max_overlap, ov)
            jac = jaccard(combos[i], combos[j])
            if jac > actual_max_jac:
                actual_max_jac = jac
            if ov >= 4:
                actual_ov_4_count += 1
            if ov == 3:
                ev_combo_set.add(combos[i])
                ev_combo_set.add(combos[j])
                
    counts = Counter()
    for c in combos:
        counts.update(c)
        
    actual_max_freq = max(counts.values()) if counts else 0
    cap = int(M * p_max)
    
    audit_results["metrics"]["actual_max_overlap"] = actual_max_overlap
    audit_results["metrics"]["overlap_4_count"] = actual_ov_4_count
    audit_results["metrics"]["ev_combo_count"] = len(ev_combo_set)
    audit_results["metrics"]["max_freq"] = actual_max_freq
    audit_results["metrics"]["freq_cap"] = cap
    audit_results["metrics"]["max_jaccard"] = actual_max_jac
    
    if actual_ov_4_count == 0:
        audit_results["checks"].append({"id": "HARD_OVERLAP_4+", "status": "PASS", "reason": "0 count"})
    else:
        audit_results["checks"].append({"id": "HARD_OVERLAP_4+", "status": "FAIL", "reason": f"Count={actual_ov_4_count}"})
        
    if len(ev_combo_set) <= ev_slots_max:
         audit_results["checks"].append({"id": "EV_SLOT_CAP", "status": "PASS", "reason": f"Used={len(ev_combo_set)} <={ev_slots_max}"})
    else:
         audit_results["checks"].append({"id": "EV_SLOT_CAP", "status": "FAIL", "reason": f"Used={len(ev_combo_set)} > {ev_slots_max}"})
         
    if actual_max_freq <= cap:
        audit_results["checks"].append({"id": "FREQ_CAP", "status": "PASS", "reason": f"{actual_max_freq} <= {cap}"})
    else:
        audit_results["checks"].append({"id": "FREQ_CAP", "status": "FAIL", "reason": f"{actual_max_freq} > {cap}"})

    # MD consistency check
    if md_stats.get("max_overlap") != actual_max_overlap:
        audit_results["checks"].append({"id": "MD_STAT_OVERLAP", "status": "FAIL", "reason": "MD mismatch"})
        
        
    # 2-D) Engine-based operations
    eng_counts = Counter(engines_list)
    fb_count = eng_counts.get("RandomFallback", 0)
    audit_results["metrics"]["fallback_count"] = fb_count
    audit_results["metrics"]["engine_distribution"] = dict(eng_counts)
    
    if fb_count <= fallback_max:
        audit_results["checks"].append({"id": "FALLBACK_LIMIT", "status": "PASS", "reason": f"{fb_count} <= {fallback_max}"})
    else:
        audit_results["checks"].append({"id": "FALLBACK_LIMIT", "status": "FAIL", "reason": f"{fb_count} > {fallback_max}"})
        
    sel_path = latest_dir / "ENGINE_SELECTION_TEMPLATE.json"
    if sel_path.exists():
        audit_results["checks"].append({"id": "ENGINE_STRATEGY", "status": "PASS", "reason": "Strategy file present"})
    else:
        audit_results["checks"].append({"id": "ENGINE_STRATEGY", "status": "FAIL", "reason": "Strategy layer missing"})

    all_pass = all(c["status"] == "PASS" for c in audit_results["checks"])
    audit_results["conclusion"] = "PASS" if all_pass else "FAIL"
    
    # 3) Report Generation
    with open(latest_dir / f"AUDIT_R{target_round}_M{M}.json", "w", encoding='utf-8') as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)
        
    md_out = [
        f"# AUDIT_R{target_round}_M{M}.md",
        f"**Conclusion:** {audit_results['conclusion']}",
        "",
        "## Top Risks & Corrections",
        "1. RandomFallback 비율: 해당 한도를 초과할 경우 전략 엔진 점유율 보강 필요." if fb_count > fallback_max else "1. 특이사항 없음 (PASS 기록)",
        "2. EV 슬롯 제한: 공유 3개 조합 수가 너무 많으면 허용범위 초과 (FAIL시 수정: Jaccard 조정 등)" if len(ev_combo_set) > ev_slots_max else "",
        "3. Hard Overlap >=4 위반: 로직 결함, 발생 시 수정 최우선 순위" if actual_ov_4_count > 0 else "",
        "",
        "## Checklist",
        "| Check ID | Status | Reason |",
        "|----------|--------|--------|"
    ]
    for c in audit_results["checks"]:
        md_out.append(f"| {c['id']} | {c['status']} | {c['reason']} |")
        
    md_out.extend([
        "",
        "## Core Metrics (Recalculated)",
        f"- Max Overlap: {actual_max_overlap}",
        f"- Overlap >= 4 Count: {actual_ov_4_count}",
        f"- EV Combo Count (Overlap=3 involved): {len(ev_combo_set)}",
        f"- Max Number Frequency: {actual_max_freq} / Cap: {cap}",
        f"- Max Jaccard Seen: {actual_max_jac:.3f}",
        f"- RandomFallback Count: {fb_count}",
        "",
        "## Engine Distribution (Actual)",
    ])
    for k, v in eng_counts.items():
        md_out.append(f"- {k}: {v}")
        
    md_out.extend([
        "",
        "## EV Combinations (Involved in overlap=3)",
    ])
    for c in ev_combo_set:
        md_out.append(f"- {list(c)}")
        
    out_md_path = latest_dir / f"AUDIT_R{target_round}_M{M}.md"
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_out))
        
    history_md = Path(str(out_md_path).replace("latest", "history").replace(".md", f"_{int(datetime.now().timestamp())}.md"))
    history_md.parent.mkdir(parents=True, exist_ok=True)
    with open(history_md, "w", encoding="utf-8") as f:
         f.write("\n".join(md_out))

    print(f"[*] Audit Complete. Status: {audit_results['conclusion']} (Saved to {out_md_path})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--M", type=int, required=True)
    parser.add_argument("--p_max", type=float, default=0.16)
    parser.add_argument("--ev_slots_max", type=int, default=5)
    parser.add_argument("--fallback_max", type=int, default=5)
    args = parser.parse_args()
    
    run_audit(args.round, args.M, args.p_max, args.ev_slots_max, args.fallback_max)
