import argparse
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict

# Adjust path to import nt_lotto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from nt_lotto.nt_core.constants import EVAL_DIR, K_EVAL
from nt_lotto.nt_core.ssot import load_ssot_sorted, load_ssot_ordered, load_exclude_rounds, apply_exclusion
from nt_lotto.nt_core.metrics import recall_at_k, summarize_recalls
from nt_lotto.nt_engines.registry import get_engines

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def run_evaluation(start_round: int, end_round: int):
    print(f"[INFO] Starting Evaluation K={K_EVAL} for rounds {start_round}~{end_round}")
    
    # 1. Load Data
    ssot_sorted = load_ssot_sorted()
    ssot_ordered = load_ssot_ordered()
    excludes = load_exclude_rounds()
    
    # Apply exclusions globally?? 
    # Usually we apply exclusion to TRAIN data. 
    # TEST data (the round being predicted) validity checks:
    # If the target round itself is excluded, we skip evaluation.
    
    # Prepare results container
    # { engine_id: [recall_t1, recall_t2, ...] }
    engine_results: Dict[str, List[float]] = {e.engine_id: [] for e in get_engines()}
    engine_eval_counts: Dict[str, int] = {e.engine_id: 0 for e in get_engines()}
    
    engines = get_engines()
    
    # 2. Iterate Rounds
    valid_rounds = [
        r for r in range(start_round, end_round + 1)
        if r not in excludes
    ]
    
    # Filter SSOT to relevant range mostly for quick check, but fit needs history
    
    results_summary = []

    for t in valid_rounds:
        # 2.1 Prepare Data
        # Test Data: round t
        row_t = ssot_sorted[ssot_sorted['round'] == t]
        if row_t.empty:
            print(f"[WARN] Round {t} not found in SSOT. Skipping.")
            continue
            
        win_numbers = set(row_t.iloc[0][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.astype(int))
        
        # Train Data: round < t, excluding banned rounds
        train_sorted = ssot_sorted[ssot_sorted['round'] < t].copy()
        train_sorted = apply_exclusion(train_sorted, excludes)
        
        train_ordered = ssot_ordered[ssot_ordered['round'] < t].copy()
        train_ordered = apply_exclusion(train_ordered, excludes)
        
        # Output directory
        round_eval_dir = os.path.join(EVAL_DIR, str(t))
        ensure_dir(round_eval_dir)
        
        round_topk_data = [] # List of dicts
        round_recalls = {}
        
        # 2.2 Run Engines
        for engine in engines:
            # Fit
            # Optimization: Some engines might not need refitting every round if they are simple laws
            # But strictly following walk-forward:
            engine.fit(train_sorted, train_ordered if engine.required_ssot in ["ordered", "both"] else None)
            
            # Predict
            top_k = engine.topk_numbers(K_EVAL)
            top_k_set = set(top_k)
            
            # Metric
            # If top_k is empty (Stub), recall is NaN or 0? 
            # Stub returns [], so Intersection is 0. Recall is 0.
            # But strictly, if engine didn't run, maybe NaN? 
            # Let's count it as 0 for now, but mark status.
            
            if not top_k:
                recall = 0.0 # Or np.nan
                status = "STUB/EMPTY"
            else:
                recall = recall_at_k(top_k_set, win_numbers)
                status = "OK"
                
            engine_results[engine.engine_id].append(recall)
            engine_eval_counts[engine.engine_id] += 1
            
            round_topk_data.append({
                "engine_id": engine.engine_id,
                "top_k": str(list(top_k)), 
                "recall": recall,
                "status": status
            })
            round_recalls[engine.engine_id] = recall

        # 2.3 Save Round Artifacts
        df_topk = pd.DataFrame(round_topk_data)
        df_topk.to_csv(os.path.join(round_eval_dir, f"engine_topk_K{K_EVAL}.csv"), index=False)
        
        # Generate README
        with open(os.path.join(round_eval_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(f"# Evaluation Report: Round {t}\n\n")
            f.write(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Win Numbers**: {sorted(list(win_numbers))}\n")
            f.write(f"- **Train Size**: {len(train_sorted)} rounds\n")
            f.write(f"- **K_EVAL**: {K_EVAL}\n\n")
            f.write("## Engine Performance\n")
            f.write(df_topk.to_markdown(index=False))
            
        print(f"[{t}] Evaluated {len(engines)} engines.")

    # 3. Final Summary
    summary_rows = []
    
    for eid in engine_results:
        recalls = engine_results[eid]
        stats = summarize_recalls(recalls)
        summary_rows.append({
            "engine_id": eid,
            "status": "ACTIVE" if any(recalls) else "STUB", # crude check
            "n_rounds": len(recalls),
            "overall": f"{stats['overall']:.4f}",
            "recent10": f"{stats['recent10']:.4f}",
            "recent20": f"{stats['recent20']:.4f}",
            "recent30": f"{stats['recent30']:.4f}"
        })
        
    df_summary = pd.DataFrame(summary_rows)
    summary_path = os.path.join(EVAL_DIR, f"summary_engine_recall_K{K_EVAL}.md")
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Engine Recall@{K_EVAL} Summary\n\n")
        f.write(f"- **Evaluated Range**: {start_round} ~ {end_round}\n")
        f.write(f"- **Excluded Rounds**: {len(excludes)}\n")
        f.write(f"- **Note**: STUB engines return 0.0 recall.\n\n")
        f.write(df_summary.to_markdown(index=False))
        
    print(f"[SUCCESS] Evaluation Complete. Summary at: {summary_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    args = parser.parse_args()
    
    run_evaluation(args.start, args.end)
