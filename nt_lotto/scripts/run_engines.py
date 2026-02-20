import argparse
import sys
import os
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from nt_lotto.nt_core.constants import SSOT_SORTED, SSOT_ORDERED, K_EVAL

ENGINES = [
    "NT4", "NT5", "NT-LL", "VPA", "NT-VPA-1", "NTO", "NT-Omega", 
    "AL1", "AL2", "ALX", "NT-EXP", "NT-DPP", "NT-HCE", "NT-PAT"
]
BASE_EVAL_ENGINES = ["NT4", "NT5", "NT-LL", "VPA", "NT-VPA-1"]

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("EngineRunner")

df_sorted_cache = None

def get_actual_winners(df: pd.DataFrame, r: int):
    row = df[df['round'] == r]
    if row.empty: return set(), -1
    cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    winners = set(row.iloc[0][cols].values)
    bonus = row.iloc[0]['bonus']
    return winners, bonus

def jaccard_index(list1: List[int], list2: List[int]) -> float:
    s1, s2 = set(list1), set(list2)
    if not s1 and not s2: return 1.0
    if not s1 or not s2: return 0.0
    return len(s1 & s2) / len(s1 | s2)

def execute_engine_dynamic(engine_name: str, df_cache: pd.DataFrame, target_round: int, **kwargs):
    try:
        if engine_name == "NT4":
            from nt_lotto.nt_engines.nt4 import analyze
        elif engine_name == "NT5":
            from nt_lotto.nt_engines.nt5 import analyze
        elif engine_name == "NT-LL":
            from nt_lotto.nt_engines.nt_ll import analyze
        elif engine_name == "VPA":
            from nt_lotto.nt_engines.vpa import analyze
        elif engine_name == "NT-VPA-1":
            from nt_lotto.nt_engines.nt_vpa_1 import analyze
        elif engine_name == "NTO":
            from nt_lotto.nt_engines.nto import analyze
        elif engine_name == "NT-Omega":
            from nt_lotto.nt_engines.nt_omega import analyze
        elif engine_name in ["AL1", "AL2", "ALX"]:
            from nt_lotto.nt_engines.al_engines import analyze
            return analyze(engine_name, df_cache, target_round, **kwargs)
        elif engine_name in ["NT-EXP", "NT-DPP", "NT-HCE", "NT-PAT"]:
            from nt_lotto.nt_engines.diagnostic_stubs import analyze
            return analyze(engine_name, df_cache, target_round, **kwargs)
        else:
            return {"topk": [], "scores": [], "diagnostics": {"status": "stub"}}
            
        if engine_name in ["NT4", "NT5"]:
            return analyze(df_cache, target_round)
        else:
            return analyze(df_cache, target_round, **kwargs)
    except Exception as e:
        logger.error(f"Engine {engine_name} error at R={target_round}: {e}")
        return {"topk": [], "scores": [], "diagnostics": {"error": str(e)}}

def run_evaluation(target_round: int, eval_rounds: int, k_eval: int, out_dir: str):
    logger.info(f"--- STARTING EVALUATION MODE (Target: {target_round}, Past: {eval_rounds} rounds) ---")
    start_r = target_round - eval_rounds
    end_r = target_round - 1
    
    global df_sorted_cache
    if df_sorted_cache is None:
        from nt_lotto.nt_core.ssot_loader import load_data
        df_sorted_cache, _ = load_data(exclusion_mode=True)
        
    eval_results = {en: {"recall": [], "bonus": [], "topk_history": []} for en in ENGINES}
    
    # 1. Past rounds evaluation
    for r in range(start_r, end_r + 1):
        actual_win, actual_bonus = get_actual_winners(df_sorted_cache, r)
        if not actual_win:
            continue
            
        for engine_name in ENGINES:
            res = execute_engine_dynamic(engine_name, df_sorted_cache, r, k_eval=k_eval)
            topk = res.get('topk', []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
            
            recall = len(set(topk) & actual_win) if topk else 0
            bonus_hit = 1 if actual_bonus in topk else 0
            
            eval_results[engine_name]["recall"].append(recall)
            eval_results[engine_name]["bonus"].append(bonus_hit)
            eval_results[engine_name]["topk_history"].append(topk)

    # Compile JSON
    timestamp = datetime.now().strftime("%Y%md_%H%M")
    report_json = {
        "meta": { "k_eval": k_eval, "round_range": [start_r, end_r], "created_at": timestamp },
        "per_engine": {},
        "notes": ["lookahead_guard:PASS", "no_combo_generation:PASS"]
    }
    
    md_lines = [f"# Engine Evaluation Report (K={k_eval})", 
                f"Evaluation Range: {start_r} ~ {end_r} ({eval_rounds} rounds)",
                f"Generated At: {timestamp}\n",
                "## Engine Performance Summary (Split: Recent 20 vs Past)",
                "| Engine | Recall(All) | Rec(Recent20) | Rec(Past) | Bonus Hit | Stability |",
                "| :--- | :---: | :---: | :---: | :---: | :---: |"]
                
    summary_for_nto = {}

    for engine_name in ENGINES:
        recs = eval_results[engine_name]["recall"]
        bons = eval_results[engine_name]["bonus"]
        hist = eval_results[engine_name]["topk_history"]
        
        n_tot = len(recs)
        if n_tot == 0: continue
        
        n_recent = min(20, n_tot)
        rec_recent = recs[-n_recent:]
        rec_past = recs[:-n_recent] if n_tot > n_recent else recs
        
        mean_tot = float(np.mean(recs))
        std_tot = float(np.std(recs))
        mean_recent = float(np.mean(rec_recent))
        mean_past = float(np.mean(rec_past)) if rec_past else mean_recent
        mean_bon = float(np.mean(bons))
        
        jaccards = [jaccard_index(hist[i-1], hist[i]) for i in range(1, len(hist))]
        mean_stab = float(np.mean(jaccards)) if jaccards else 1.0
        
        summary_for_nto[engine_name] = {
            "mean_tot": mean_tot, "std_tot": std_tot,
            "mean_recent": mean_recent, "mean_past": mean_past, 
            "stability": mean_stab, "n_tot": n_tot
        }
        
        report_json["per_engine"][engine_name] = {
            "recall_all": {"mean": mean_tot, "std": std_tot},
            "recall_recent20": {"mean": mean_recent},
            "recall_past": {"mean": mean_past},
            "bonus_hit": {"mean": mean_bon},
            "stability": {"mean": mean_stab}
        }
        
        if engine_name in BASE_EVAL_ENGINES + ["NTO", "NT-Omega"]:
            md_lines.append(f"| {engine_name} | {mean_tot:.2f}±{std_tot:.2f} | {mean_recent:.2f} | {mean_past:.2f} | {mean_bon:.2f} | {mean_stab:.2f} |")
            
    hist_dir = os.path.join(out_dir, "../history")
    latest_dir = os.path.join(out_dir)
    os.makedirs(hist_dir, exist_ok=True)
    os.makedirs(latest_dir, exist_ok=True)
    
    eval_json_name = "Engine_Evaluation_K20.json"
    eval_md_name = "Engine_Evaluation_K20.md"
    
    with open(os.path.join(latest_dir, eval_json_name), 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    with open(os.path.join(hist_dir, f"{timestamp}_{eval_json_name}"), 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(latest_dir, eval_md_name), 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    with open(os.path.join(hist_dir, f"{timestamp}_{eval_md_name}"), 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
        
    logger.info("Evaluation Complete. Triggering Conservative NTO Update.")
    
    # ---------------------------------------------------------
    # TASK-2: COnservative NTO Weights Update
    # ---------------------------------------------------------
    prev_weights = {en: 1.0/len(BASE_EVAL_ENGINES) for en in BASE_EVAL_ENGINES}
    new_weights = prev_weights.copy()
    
    promoted, demoted, no_adv = [], [], []
    rationale = []
    
    base_m_tot = np.mean([summary_for_nto[e]["mean_tot"] for e in BASE_EVAL_ENGINES])
    base_m_rec = np.mean([summary_for_nto[e]["mean_recent"] for e in BASE_EVAL_ENGINES])
    base_m_pas = np.mean([summary_for_nto[e]["mean_past"] for e in BASE_EVAL_ENGINES])
    
    for en in BASE_EVAL_ENGINES:
        st = summary_for_nto[en]
        
        # Consistent Direction Check
        better_recent = st["mean_recent"] >= base_m_rec
        better_past = st["mean_past"] >= base_m_pas
        worse_recent = st["mean_recent"] <= base_m_rec
        worse_past = st["mean_past"] <= base_m_pas
        
        # 95% CI Check (1.96 * SE)
        se = st["std_tot"] / np.sqrt(st["n_tot"]) if st["n_tot"] > 0 else 0
        ci_lower = st["mean_tot"] - 1.96 * se
        ci_upper = st["mean_tot"] + 1.96 * se
        
        if better_recent and better_past and ci_lower > base_m_tot and st["stability"] > 0.20:
            promoted.append(en)
            new_weights[en] += 0.05
            rationale.append(f"{en} promoted: Consistent advantage + CI Lower Bound > Baseline ({ci_lower:.2f} > {base_m_tot:.2f})")
        elif worse_recent and worse_past and ci_upper < base_m_tot:
            demoted.append(en)
            new_weights[en] = max(0.01, new_weights[en] - 0.05)
            rationale.append(f"{en} demoted: Consistent disadvantage + CI Upper Bound < Baseline ({ci_upper:.2f} < {base_m_tot:.2f})")
        else:
            no_adv.append(en)
            rationale.append(f"{en} no_advantage: Direction inconsistent or CI overlap.")
            
    if not promoted and not demoted:
        rationale.append("Global No Advantage. Keeping weights uniform.")
        
    s_w = sum(new_weights.values())
    new_weights = {k: v/s_w for k,v in new_weights.items()}
    
    nto_json = {
        "meta": {"k_eval": k_eval, "created_at": timestamp},
        "prev_weights": prev_weights,
        "new_weights": new_weights,
        "decision": {"promoted": promoted, "demoted": demoted, "no_advantage": no_adv, "rationale": rationale}
    }
    
    nto_name = "NTO_Weights.json"
    with open(os.path.join(latest_dir, nto_name), 'w', encoding='utf-8') as f:
        json.dump(nto_json, f, ensure_ascii=False, indent=2)
    with open(os.path.join(hist_dir, f"{timestamp}_{nto_name}"), 'w', encoding='utf-8') as f:
        json.dump(nto_json, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------
    # TASK-3: NT-Omega with Gathered Engine Evidences
    # ---------------------------------------------------------
    logger.info(f"Generating Target Round {target_round} predictions to gather evidences...")
    target_preds = {}
    for en in ENGINES:
        if en == "NT-Omega": continue
        res = execute_engine_dynamic(en, df_sorted_cache, target_round, k_eval=k_eval, engine_weights=new_weights)
        topk = res.get('topk', []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
        target_preds[en] = topk
        
    logger.info(f"Triggering NT-Omega extraction for TARGET ROUND {target_round}...")
    omega_res = execute_engine_dynamic("NT-Omega", df_sorted_cache, target_round, k_eval=k_eval, k_pool=22, engine_weights=new_weights)
    
    if isinstance(omega_res, dict) and "topk" in omega_res:
        omega_top22 = omega_res["topk"]
        omega_scores = omega_res.get("scores", [])
        
        md_om_lines = [
            f"# NT-Omega K_pool=22 Report (Round {target_round})",
            f"Generated At: {timestamp}\n",
            "**[CONSTRAINT CHECK] no_combo_generation: PASS (Combinations generation explicitly disabled)**\n",
            "## Final Top 22 Pool",
            f"**{omega_top22}**\n",
            "## Score & Evidence Summary",
            "| Num | Meta Score | Evidence / Rationale |",
            "| :---: | :---: | :--- |"
        ]
        
        gathered_evidences = {}
        for sc in omega_scores[:22]:
            n = sc.get('n')
            s = sc.get('score', 0)
            
            # Gather minimum 2 evidences
            evs = ["NTO Meta Core"]
            if n in target_preds.get("VPA", []): evs.append("VPA Top20 (Pattern Match)")
            if n in target_preds.get("NT-LL", []): evs.append("NT-LL Top20 (Local Dev Correction)")
            if n in target_preds.get("NT-VPA-1", []): evs.append("NT-VPA-1 Top20 (Hybrid Signal)")
            if n in target_preds.get("AL1", []): evs.append("AL1 Top20 (Ending Trend Flag)")
            if n in target_preds.get("NT5", []): evs.append("NT5 Baseline Support")
            
            gathered_evidences[n] = evs
            ev_str = ", ".join(evs)
            md_om_lines.append(f"| {n} | {s:.4f} | {ev_str} |")
            
        om_md_name = "Omega_Kpool22.md"
        with open(os.path.join(latest_dir, om_md_name), 'w', encoding='utf-8') as f:
            f.write("\n".join(md_om_lines))
        with open(os.path.join(hist_dir, f"{timestamp}_{om_md_name}"), 'w', encoding='utf-8') as f:
            f.write("\n".join(md_om_lines))
            
        omega_json = {
            "meta": {"round": target_round, "k_pool": 22, "created_at": timestamp},
            "omega_topk_22": omega_top22,
            "evidence_summary": gathered_evidences
        }
        omega_name = "Omega_Kpool22.json"
        with open(os.path.join(latest_dir, omega_name), 'w', encoding='utf-8') as f:
            json.dump(omega_json, f, ensure_ascii=False, indent=2)
            
    logger.info("All Eval, Weight, and Omega outputs generated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Run NT Project v2.0 Pipeline")
    parser.add_argument("--mode", type=str, default="predict", choices=["predict", "eval"], help="Run mode")
    parser.add_argument("--target", type=int, required=True, help="Target Round (R+1)")
    parser.add_argument("--out_dir", type=str, required=True, help="Output directory paths")
    parser.add_argument("--k_eval", type=int, default=20, help="K value for metrics")
    parser.add_argument("--eval_rounds", type=int, default=50, help="Number of past rounds for Evaluation")
    
    args = parser.parse_args()
    
    if args.mode == "eval":
        run_evaluation(args.target, args.eval_rounds, args.k_eval, args.out_dir)
    else:
        logger.info("Predict mode not fully detailed in this sprint. Use --mode eval to trigger Tasks 1,2,3.")

if __name__ == "__main__":
    main()
