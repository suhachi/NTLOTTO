import sys
import os
import argparse
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from nt_lotto.nt_core.constants import K_EVAL, K_POOL, EVAL_DIR, ARCHIVE_DIR, SSOT_SORTED
from nt_lotto.nt_core.ssot import load_ssot_sorted, load_ssot_ordered, load_exclude_rounds, apply_exclusion
from nt_lotto.nt_core.omega import (
    softmax_weights, build_candidate_pool, EngineKPI, OmegaWeight, 
    DEFAULT_COEFFS, DEFAULT_TAU, MIN_WEIGHT, MAX_WEIGHT_CAP
)
from nt_lotto.nt_engines.registry import get_engines

def load_evaluation_summary() -> List[EngineKPI]:
    """
    Load the latest summary_engine_recall_K20.md and parse it.
    """
    summary_path = os.path.join(EVAL_DIR, f"summary_engine_recall_K{K_EVAL}.md")
    if not os.path.exists(summary_path):
        print(f"[WARN] Summary not found at {summary_path}. Returning empty/stubs.")
        return []
        
    kpis = []
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_table = False
        for line in lines:
            if line.strip().startswith("| engine_id"):
                in_table = True
                continue
            if in_table and line.strip().startswith("|---"):
                continue
            if in_table and line.strip().startswith("|"):
                # Split by | and filter empty strings
                cols = [c.strip() for c in line.split("|")]
                # Assuming table format: | engine_id | status | n_rounds | overall | ... |
                # split("|") -> ["", "NT4", "STUB", ...]
                # valid content starts at index 1
                
                # Filter out empty strings from the ends
                cols = [c for c in cols if c]
                
                if len(cols) >= 6:
                    kpi = EngineKPI(
                        engine_id=cols[0],
                        status=cols[1],
                        n_eval_rounds=int(cols[2]),
                        overall=float(cols[3]),
                        recent10=float(cols[4]),
                        recent20=float(cols[5]),
                        recent30=float(cols[6])
                    )
                    kpis.append(kpi)
    except Exception as e:
        print(f"[ERROR] Failed parsing summary table: {e}")
        return []
                
    return kpis

def run_omega_pool(target_round: int, train_end_round: int):
    print(f"[INFO] Omega Pool Gen: Target={target_round}, TrainEnd={train_end_round}")
    print(f"[INFO] Config: K_EVAL={K_EVAL}, K_POOL={K_POOL}, Tau={DEFAULT_TAU}")
    
    # 1. Load KPIs & Compute Weights
    kpis = load_evaluation_summary()
    
    # If no KPIs found (or stub run), generate placeholders
    if not kpis:
        engines = get_engines()
        kpis = [
            EngineKPI(e.engine_id, "STUB", 0.0, 0.0, 0.0, 0.0, 0)
            for e in engines
        ]

    # Compute Weights
    weights = softmax_weights(kpis, tau=DEFAULT_TAU)
    
    # Save Weights Artifacts
    weights_dir = EVAL_DIR
    if not os.path.exists(weights_dir):
        os.makedirs(weights_dir)
        
    # JSON
    w_data = [
        {
            "engine_id": w.engine_id,
            "weight": w.weight,
            "raw_kpi": w.raw_kpi,
            "gated": w.is_gated,
            "reason": w.gate_reason
        } 
        for w in weights
    ]
    with open(os.path.join(weights_dir, f"omega_weights_K{K_EVAL}.json"), "w") as f:
        json.dump({
            "meta": {
                "tau": DEFAULT_TAU,
                "coeffs": DEFAULT_COEFFS,
                "generated_at": str(datetime.now())
            },
            "weights": w_data
        }, f, indent=2)
        
    # MD
    w_df = pd.DataFrame([
        {
            "Engine": w.engine_id,
            "Weight": f"{w.weight:.4f}",
            "KPI": f"{w.raw_kpi:.4f}", 
            "Gated": "YES" if w.is_gated else "NO"
        }
        for w in weights
    ])
    
    with open(os.path.join(weights_dir, f"omega_weights_K{K_EVAL}.md"), "w", encoding="utf-8") as f:
        f.write(f"# Omega Weights (K={K_EVAL})\n\n")
        f.write(f"- **Tau**: {DEFAULT_TAU}\n")
        f.write(f"- **Min Floor**: {MIN_WEIGHT}, **Max Cap**: {MAX_WEIGHT_CAP}\n\n")
        f.write(w_df.to_markdown(index=False))
        
    # 2. Run Engines for Target Round
    ssot_sorted = load_ssot_sorted()
    ssot_ordered = load_ssot_ordered()
    excludes = load_exclude_rounds()
    
    # Train Data
    train_sorted = ssot_sorted[ssot_sorted['round'] <= train_end_round].copy()
    train_sorted = apply_exclusion(train_sorted, excludes)
    
    train_ordered = ssot_ordered[ssot_ordered['round'] <= train_end_round].copy()
    train_ordered = apply_exclusion(train_ordered, excludes)
    
    # Engine Outputs
    engine_topk = {}
    
    engines = get_engines()
    
    pool_out_dir = os.path.join(ARCHIVE_DIR, "Omega_Pools", str(target_round))
    if not os.path.exists(pool_out_dir):
        os.makedirs(pool_out_dir)

    topk_rows = []

    for engine in engines:
        # Fit
        engine.fit(train_sorted, train_ordered if engine.required_ssot in ["ordered", "both"] else None)
        
        # Predict
        top_k = engine.topk_numbers(K_EVAL)
        engine_topk[engine.engine_id] = top_k
        
        topk_rows.append({
            "engine_id": engine.engine_id,
            "top_k": str(top_k),
            "count": len(top_k)
        })
        
    # Save Engine TopK
    pd.DataFrame(topk_rows).to_csv(os.path.join(pool_out_dir, f"engine_topk_K{K_EVAL}.csv"), index=False)
    
    # 3. Build Pool
    pool_nums, pool_df = build_candidate_pool(engine_topk, weights, K_EVAL, K_POOL)
    
    # Save Pool
    if pool_df.empty:
        # Create empty CSV with headers if pool is empty
        pool_df = pd.DataFrame(columns=["number", "score", "support", "avg_rank", "engines"])
    
    pool_df.to_csv(os.path.join(pool_out_dir, f"omega_pool_K{K_POOL}.csv"), index=False)
    
    # Weights snapshot in pool dir
    with open(os.path.join(pool_out_dir, "omega_weights.json"), "w") as f:
        json.dump(w_data, f, indent=2)
        
    # README
    with open(os.path.join(pool_out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# Omega Candidate Pool: Round {target_round}\n\n")
        f.write(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Train Range**: ~ {train_end_round}\n")
        f.write(f"- **Pool Size**: {K_POOL}\n")
        f.write(f"- **Active Engines**: {len([w for w in weights if w.weight > 0])}\n")
        f.write(f"- **Engine Status**: {len(engines)} engines loaded ({len([k for k in kpis if k.status != 'STUB'])} active)\n\n")
        f.write("## Pool Numbers\n")
        f.write(f"`{pool_nums}`\n\n")
        f.write("## Details\n")
        if not pool_df.empty:
            f.write(pool_df.to_markdown(index=False))
        else:
            f.write("(Pool is empty - Likely all engines are STUB/Empty)")
        f.write("\n\n## Note\n")
        f.write("- **No 50-Combo Generation**: This artifact contains only the candidate pool.\n")
        f.write("- **SSOT**: Derived from `ssot_sorted.csv` (Label) and `ssot_ordered.csv` (Feature).\n")

    print(f"[SUCCESS] Omega Pool Generated at {pool_out_dir}")
    print(f"Pool: {pool_nums}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, required=True)
    parser.add_argument("--train_end", type=int, required=True)
    args = parser.parse_args()
    
    run_omega_pool(args.target, args.train_end)
