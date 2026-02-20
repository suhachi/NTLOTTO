import argparse
import sys
import os
import logging
import pandas as pd
import numpy as np
import itertools
from collections import Counter
import math
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from nt_lotto.nt_core.ssot_loader import load_data

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("GenerateCombosV2")

def get_engine_results(df_sorted, r, k_eval):
    results = {}
    engines = ["NT-Omega", "NTO", "NT-VPA-1", "NT5", "NT-LL", "NT4", "VPA"]
    
    for engine_name in engines:
        try:
            if engine_name == "NT4":
                from nt_lotto.nt_engines.nt4 import analyze
                results[engine_name] = analyze(df_sorted, r)
            elif engine_name == "NT5":
                from nt_lotto.nt_engines.nt5 import analyze
                results[engine_name] = analyze(df_sorted, r)
            elif engine_name == "NT-LL":
                from nt_lotto.nt_engines.nt_ll import analyze
                res = analyze(df_sorted, r)
                if isinstance(res, list):
                    scores = [{"n": n, "score": 1.0 - (i/len(res))} for i, n in enumerate(res)]
                    results[engine_name] = {"topk": res, "scores": scores}
                else:
                    results[engine_name] = res
            elif engine_name == "VPA":
                from nt_lotto.nt_engines.vpa import analyze
                results[engine_name] = analyze(df_sorted, r)
            elif engine_name == "NT-VPA-1":
                from nt_lotto.nt_engines.nt_vpa_1 import analyze
                results[engine_name] = analyze(df_sorted, r, k_eval=45)
            elif engine_name == "NTO":
                from nt_lotto.nt_engines.nto import analyze
                results[engine_name] = analyze(df_sorted, r, k_eval=45)
            elif engine_name == "NT-Omega":
                from nt_lotto.nt_engines.nt_omega import analyze
                results[engine_name] = analyze(df_sorted, r, k_eval=45, k_pool=22)
        except Exception as e:
            logger.warning(f"Error running {engine_name}: {e}")
            results[engine_name] = {"topk": [], "scores": []}
            
    return results

def get_norm_score_map(res):
    if isinstance(res, list):
        topk = res
        if not topk: return {n: 0.0 for n in range(1, 46)}
        return {n: 1.0 - (i/len(topk)) for i, n in enumerate(topk)}
        
    scores = res.get("scores", [])
    if not scores:
        topk = res.get("topk", [])
        if not topk: return {n: 0.0 for n in range(1, 46)}
        return {n: 1.0 - (i/len(topk)) for i, n in enumerate(topk)}
    
    score_map = {item['n']: item['score'] for item in scores}
    if not score_map: return {n: 0.0 for n in range(1, 46)}
    
    min_s = min(score_map.values())
    max_s = max(score_map.values())
    
    if max_s > min_s:
        sm = {k: (v - min_s)/(max_s - min_s) for k, v in score_map.items()}
    else:
        sm = {k: 1.0 for k in score_map.keys()}
        
    # Fill missing with 0.0
    for n in range(1, 46):
        if n not in sm: sm[n] = 0.0
    return sm

def build_candidate_pool(engines_res, pool_min_size, nto_topk_for_pool):
    omega_top22 = engines_res["NT-Omega"].get("topk", [])[:22]
    nto_top_n = engines_res["NTO"].get("topk", [])[:nto_topk_for_pool]
    
    pool_set = set(omega_top22)
    
    # Add from NTO up to 11
    added_nto = 0
    for n in nto_top_n:
        if n not in pool_set and added_nto < 11:
            pool_set.add(n)
            added_nto += 1
            if len(pool_set) >= pool_min_size:
                break
                
    # If still not enough, add from NT-VPA-1
    if len(pool_set) < pool_min_size:
        vpa1_top = engines_res["NT-VPA-1"].get("topk", [])[:45]
        for n in vpa1_top:
            if n not in pool_set:
                pool_set.add(n)
                if len(pool_set) >= pool_min_size:
                    break
                    
    # Ultimate fallback just in case: add sequentially from 1..45
    if len(pool_set) < pool_min_size:
        for n in range(1, 46):
            if n not in pool_set:
                pool_set.add(n)
                if len(pool_set) >= pool_min_size:
                    break
                    
    return sorted(list(pool_set))

def get_quota(M, allocation):
    quotas = {}
    for e, w in allocation.items():
        quotas[e] = round(M * w)
        
    # Minimum 1 for NT4, VPA, NT-LL if allocation > 0
    for e in ["NT4", "VPA", "NT-LL"]:
        if allocation.get(e, 0) > 0 and quotas.get(e, 0) == 0:
            quotas[e] = 1
            
    diff = M - sum(quotas.values())
    # Adjust starting from highest allocation
    sorted_engs_desc = sorted(allocation.keys(), key=lambda x: -allocation[x])
    sorted_engs_asc = sorted(allocation.keys(), key=lambda x: allocation[x])
    
    while diff > 0:
        for e in sorted_engs_desc:
            if diff == 0: break
            quotas[e] += 1
            diff -= 1
    while diff < 0:
        for e in sorted_engs_asc:
            if diff == 0: break
            if quotas[e] > 1: # keep min 1 if possible
                quotas[e] -= 1
                diff += 1
                
    return quotas

def calculate_cap(M, pool_size, slack):
    return math.ceil((6 * M) / pool_size * (1 + slack))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--M", type=int, default=60)
    parser.add_argument("--plan", type=str, default="aggressive")
    parser.add_argument("--k_eval", type=int, default=20)
    parser.add_argument("--nto_topk_for_pool", type=int, default=30)
    parser.add_argument("--pool_min_size", type=int, default=33)
    parser.add_argument("--cap_slack", type=float, default=0.15)
    parser.add_argument("--global_exception_slots", type=int, default=5)
    parser.add_argument("--overlap_global_hard", type=int, default=5)
    parser.add_argument("--overlap_global_soft", type=int, default=4)
    parser.add_argument("--overlap_intra_hard", type=int, default=4)
    parser.add_argument("--overlap_intra_exception_topq", type=float, default=0.10)
    parser.add_argument("--overlap_intra_exception_ratio", type=float, default=0.15)
    parser.add_argument("--engine_topk_fallback", type=int, default=35)
    parser.add_argument("--resample_attempts", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20260221)
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    
    df_sorted, _ = load_data(exclusion_mode=True)
    df_past = df_sorted[df_sorted['round'] < args.round].copy()
    
    engines_res = get_engine_results(df_past, args.round, args.k_eval)
    
    allocation = {
        "NT-Omega": 0.48, "NTO": 0.18, "NT-VPA-1": 0.12, "NT5": 0.12, 
        "NT-LL": 0.05, "NT4": 0.025, "VPA": 0.025
    }
    
    norm_maps = {e: get_norm_score_map(res) for e, res in engines_res.items()}
    
    # 3. Build Candidate Pool
    pool_c = build_candidate_pool(engines_res, args.pool_min_size, args.nto_topk_for_pool)
    if len(pool_c) < args.pool_min_size:
        logger.error(f"FATAL: Candidate pool size {len(pool_c)} < {args.pool_min_size}. Exiting.")
        sys.exit(1)
        
    cap = calculate_cap(args.M, len(pool_c), args.cap_slack)
    
    # 4. Quota
    quotas = get_quota(args.M, allocation)
    logger.info(f"M={args.M}, Pool_Size={len(pool_c)}, Cap={cap}")
    logger.info(f"Quotas: {quotas}")
    
    # 5. Global generation state
    seen_combos = set()
    num_counts = Counter()
    global_exceptions_used = 0
    max_global_exc = args.global_exception_slots
    exc_logs = []
    
    engine_groups = {e: [] for e in allocation.keys()}
    
    # Generate all combinations in C and score them
    all_possible = list(itertools.combinations(pool_c, 6))
    
    class ExceptionFull(Exception): pass
    
    for e in allocation.keys():
        q_target = quotas[e]
        if q_target == 0: continue
        
        e_smap = norm_maps.get(e, {})
        def score_combo(c):
            return sum(e_smap.get(n, 0.0) for n in c)
            
        scored_combos = [(score_combo(c), c) for c in all_possible]
        # sort desc by score, desc by lexicographic (for tie breaks if needed, keeping deterministic)
        scored_combos.sort(key=lambda x: (-x[0], x[1]))
        
        sorted_pool = [x[1] for x in scored_combos]
        engine_exc_max = max(1, math.ceil(q_target * args.overlap_intra_exception_ratio))
        engine_exc_used = 0
        top10_idx_threshold = int(len(sorted_pool) * args.overlap_intra_exception_topq)
        
        e_combos = []
        # Attempt generation
        # Pass 1: Strict Check
        for idx, c in enumerate(sorted_pool):
            if len(e_combos) == q_target: break
            if c in seen_combos: continue
            
            intra_ov = max([len(set(c) & set(ex)) for ex in e_combos] + [0])
            global_ov = max([len(set(c) & set(ex)) for ex in seen_combos] + [0])
            freq_vio = any(num_counts[n] + 1 > cap for n in c)
            
            if intra_ov >= args.overlap_intra_hard or global_ov >= args.overlap_global_soft or freq_vio:
                continue
                
            e_combos.append(c)
            seen_combos.add(c)
            for n in c: num_counts[n] += 1
            
        # Pass 2: Fallback (Exceptions & Pool Expand)
        if len(e_combos) < q_target:
            # Try exceptions
            for idx, c in enumerate(sorted_pool):
                if len(e_combos) == q_target: break
                if c in seen_combos: continue
                
                intra_ov = max([len(set(c) & set(ex)) for ex in e_combos] + [0])
                global_ov = max([len(set(c) & set(ex)) for ex in seen_combos] + [0])
                freq_vio = any(num_counts[n] + 1 > cap for n in c)
                
                if global_ov >= args.overlap_global_hard: # 5
                    continue
                if intra_ov >= 5: # absolute intra hard
                    continue
                    
                needs_exc = False
                reasons = []
                
                if intra_ov == 4:
                    if idx > top10_idx_threshold: continue
                    if engine_exc_used >= engine_exc_max: continue
                    needs_exc = True
                    reasons.append("intra_ov=4")
                    
                if global_ov == 4:
                    needs_exc = True
                    reasons.append("global_ov=4")
                    
                if freq_vio:
                    needs_exc = True
                    reasons.append("freq_cap")
                    
                if needs_exc:
                    if global_exceptions_used >= max_global_exc:
                        continue
                    global_exceptions_used += 1
                    if intra_ov == 4: engine_exc_used += 1
                    
                    exc_logs.append({
                        "type": '&'.join(reasons),
                        "engine": e,
                        "combo": c,
                        "reason": f"idx={idx}, intra={intra_ov}, glob={global_ov}",
                        "slot_used_index": global_exceptions_used
                    })
                
                e_combos.append(c)
                seen_combos.add(c)
                for n in c: num_counts[n] += 1

        # Pass 3: Pool Expansion (fallback to top 35 of the engine) if still not met
        if len(e_combos) < q_target:
            logger.info(f"[{e}] Quota not met ({len(e_combos)}/{q_target}). Expanding pool to engine Top35.")
            e_top35 = set(engines_res[e].get("topk", [])[:args.engine_topk_fallback])
            extended_pool = sorted(list(set(pool_c) | e_top35))
            ext_possible = list(itertools.combinations(extended_pool, 6))
            scored_ext = [(score_combo(c), c) for c in ext_possible]
            scored_ext.sort(key=lambda x: (-x[0], x[1]))
            
            for score, c in scored_ext:
                if len(e_combos) == q_target: break
                if c in seen_combos: continue
                # In expanded mode, we only do Strict Check
                intra_ov = max([len(set(c) & set(ex)) for ex in e_combos] + [0])
                global_ov = max([len(set(c) & set(ex)) for ex in seen_combos] + [0])
                freq_vio = any(num_counts[n] + 1 > cap for n in c)
                
                if intra_ov >= args.overlap_intra_hard or global_ov >= args.overlap_global_soft or freq_vio:
                    continue
                e_combos.append(c)
                seen_combos.add(c)
                for n in c: num_counts[n] += 1
                
        # If still failing, re-distribute to NT-Omega or NTO (simplified final safeguard)
        if len(e_combos) < q_target:
            shortfall = q_target - len(e_combos)
            logger.warning(f"[{e}] Still stuck. Redistributing {shortfall} quota to NT-Omega.")
            quotas["NT-Omega"] += shortfall
            quotas[e] = len(e_combos)
            
        engine_groups[e] = e_combos
        
    all_final = []
    # Verify overall
    for e in allocation.keys():
        for c in engine_groups[e]:
            all_final.append({
                "method": e, "n1": c[0], "n2": c[1], "n3": c[2], 
                "n4": c[3], "n5": c[4], "n6": c[5]
            })
            
    df_output = pd.DataFrame(all_final)
    csv_filename = f"NTUC_{args.round}_combos.csv"
    df_output.to_csv(csv_filename, index=False)
    
    df_analysis = df_output['method'].value_counts().reset_index()
    df_analysis.columns = ['method', 'count']
    df_analysis.to_csv(f"NTUC_{args.round}_analysis_by_method.csv", index=False)
    
    g_max_ov = 0
    if len(seen_combos) >= 2:
        for c1, c2 in itertools.combinations(seen_combos, 2):
            g_max_ov = max(g_max_ov, len(set(c1) & set(c2)))
            
    i_max_ov = 0
    for e, combos in engine_groups.items():
        if len(combos) >= 2:
            for c1, c2 in itertools.combinations(combos, 2):
                i_max_ov = max(i_max_ov, len(set(c1) & set(c2)))
                
    n_cnt_max = max(num_counts.values()) if num_counts else 0
    
    md_lines = [
        f"# Prediction Set R{args.round} M={args.M}",
        f"**Allocation Plan**: {args.plan.capitalize()}",
        f"**Candidate Pool C (Size {len(pool_c)})**: {pool_c}",
        f"**Dynamic Freq Cap**: {cap} (Slack: {args.cap_slack})",
        "",
        "## Quota by Method",
        "| Method | Quota | Actual |",
        "|---|---|---|"
    ]
    for e, q in quotas.items():
        actual = len(engine_groups[e])
        md_lines.append(f"| {e} | {q} | {actual} |")
        
    md_lines.extend(["", "## Constitution Adherence"])
    md_lines.append(f"- **Total Unique Combos**: {len(seen_combos)} (Expected {args.M})")
    md_lines.append(f"- **Global Max Overlap**: {g_max_ov} (Limit: 4 Soft, 5 Hard)")
    md_lines.append(f"- **Intra-engine Max Overlap**: {i_max_ov} (Limit: 3 Soft, 4 Exception, 5 Hard)")
    md_lines.append(f"- **Max Number Frequency**: {n_cnt_max} (Cap: {cap})")
    md_lines.append(f"- **Global Exceptions Used**: {global_exceptions_used} / {max_global_exc}")
    
    md_lines.append("- **Exception Logs**:")
    for log in exc_logs:
        md_lines.append(f"  - [{log['type']}] {log['engine']} combo {log['combo']} -> {log['reason']} (Slot: {log['slot_used_index']})")
        
    md_lines.extend(["", "## Combinations"])
    for e in allocation.keys():
        if not engine_groups[e]: continue
        md_lines.append(f"### {e}")
        for c in engine_groups[e]:
            md_lines.append(f"- {list(c)}")
            
    os.makedirs("docs/reports/latest", exist_ok=True)
    with open(f"docs/reports/latest/Prediction_Set_R{args.round}_M{args.M}.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    # JSON Generation
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer): return int(obj)
            if isinstance(obj, np.floating): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            return super(NpEncoder, self).default(obj)
            
    json_out = {
        "round": args.round, "M": args.M,
        "pool_C": pool_c, "pool_size": len(pool_c), "cap": cap,
        "quotas": quotas,
        "stats": {
            "unique_combos": len(seen_combos),
            "max_overlap_global": g_max_ov,
            "max_overlap_intra": i_max_ov,
            "max_number_freq": n_cnt_max,
            "exceptions_used": global_exceptions_used
        },
        "combos": all_final
    }
    with open(f"docs/reports/latest/Prediction_Set_R{args.round}_M{args.M}.json", "w", encoding="utf-8") as f:
        json.dump(json_out, f, cls=NpEncoder, indent=2, ensure_ascii=False)
        
    print(f"\npool_size={len(pool_c)}, cap={cap}")
    print(f"unique={len(seen_combos)}")
    print(f"max_overlap_global={g_max_ov}, max_overlap_intra={i_max_ov}")
    print(f"max_number_freq={n_cnt_max}")
    print(f"exceptions_used={global_exceptions_used}")
    
    print("\nquota_table:")
    for e, q in quotas.items():
        print(f"{e}: quota={q} actual={len(engine_groups[e])}")
        
if __name__ == "__main__":
    main()
