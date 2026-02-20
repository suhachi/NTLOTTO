import argparse
import sys
import os
import json
import logging
import pandas as pd
import subprocess
from dataclasses import asdict
from typing import List, Dict, Set, Optional

# Adjust path: Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import Core Constants and Functions
from nt_lotto.nt_core.constants import SSOT_SORTED, SSOT_ORDERED, EXCLUDE_CSV, K_EVAL, K_POOL
from nt_lotto.nt_core.ssot_loader import load_data as load_ssot
from nt_lotto.nt_core.ssot import load_exclude_rounds
from nt_lotto.nt_core.scoring import score_portfolio, summarize_scoreboard
from nt_lotto.nt_core.kpi import update_engine_kpi
from nt_lotto.nt_core.omega import (
    softmax_weights, 
    compute_engine_kpi,
    build_candidate_pool,
    EngineKPI,
    OmegaWeight
)

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("RoundPipeline")

def run_engines_script(target_round: int, out_dir: str):
    """
    Calls run_engines.py via subprocess to execute 14 engines.
    This separates the engine execution environment from the orchestrator.
    """
    script_path = os.path.join(os.path.dirname(__file__), "run_engines.py")
    cmd = [sys.executable, script_path, "--target", str(target_round), "--out_dir", out_dir]
    
    logger.info(f"Subprocess: Running engines for Round {target_round}...")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run engines: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="NT Operational Pipeline (Round Orchestrator)")
    parser.add_argument("--round", type=int, required=True, help="Current round (R) to Analyze/Backfill")
    parser.add_argument("--mode", type=str, choices=['backfill', 'next'], default='backfill',
                        help="Mode: backfill (score R only) or next (score R + predict R+1)")
    parser.add_argument("--out_root", type=str, default="03_Global_Analysis_Archive", help="Output root directory")
    
    args = parser.parse_args()
    
    current_round = args.round
    next_round = current_round + 1
    out_root = args.out_root
    
    # 0. Setup Directories
    round_dir = os.path.join(out_root, "Rounds", str(current_round))
    os.makedirs(round_dir, exist_ok=True)
    
    kpi_dir = os.path.join(out_root, "KPI")
    os.makedirs(kpi_dir, exist_ok=True)
    
    # 1. Load Data (SSOT)
    # This assumes Step A (import_md.py) has already run and updated SSOT.
    logger.info("Loading SSOT Data...")
    ssot_sorted, _ = load_ssot(exclusion_mode=False)
    
    # Fetch Winning Numbers for Current Round
    row = ssot_sorted[ssot_sorted['round'] == current_round]
    if row.empty:
        logger.error(f"Round {current_round} not found in SSOT. Please run 'import_md.py' first.")
        sys.exit(1)
        
    winning_numbers = {
        'n1': row.iloc[0]['n1'], 'n2': row.iloc[0]['n2'], 'n3': row.iloc[0]['n3'],
        'n4': row.iloc[0]['n4'], 'n5': row.iloc[0]['n5'], 'n6': row.iloc[0]['n6'],
        'bonus': row.iloc[0]['bonus']
    }
    winning_set = {winning_numbers[k] for k in ['n1','n2','n3','n4','n5','n6']}
    logger.info(f"Winning Numbers for R{current_round}: {winning_set} + Bonus {winning_numbers['bonus']}")

    # =========================================================
    # PHASE 1: Backfill / Score Round R
    # =========================================================
    logger.info(f"=== Phase 1: Processing Round {current_round} ===")
    
    # --- Step B: Score Portfolio (If exists) ---
    portfolio_path = os.path.join(out_root, "Portfolios", str(current_round), "portfolio_50.csv")
    if os.path.exists(portfolio_path):
        logger.info(f"Scoring Portfolio: {portfolio_path}")
        portfolio_df = pd.read_csv(portfolio_path)
        # Use winning numbers string for score_portfolio function signature
        win_str = f"{row.iloc[0]['n1']},{row.iloc[0]['n2']},{row.iloc[0]['n3']},{row.iloc[0]['n4']},{row.iloc[0]['n5']},{row.iloc[0]['n6']}"
        scored_df = score_portfolio(current_round, portfolio_df, win_str, row.iloc[0]['bonus'])
        
        score_csv = os.path.join(round_dir, f"scoring_{current_round}.csv")
        scored_df.to_csv(score_csv, index=False)
        
        summary_df = summarize_scoreboard(scored_df)
        summary_md = os.path.join(round_dir, f"summary_{current_round}.md")
        with open(summary_md, "w", encoding="utf-8") as f:
            f.write(f"# Scoring Summary Round {current_round}\n\n")
            f.write(f"- Winning: {winning_set} + {winning_numbers['bonus']}\n\n")
            f.write(summary_df.to_markdown(index=False))
            logger.info(f"Scoring Summary saved to {summary_md}")
    else:
        logger.warning(f"No portfolio found for R{current_round}. Skipping Portfolio Scoring.")

    # --- Step C: Engine Performance (Run & Score Engines) ---
    # 1. Run Engines for R (hindsight/backfill analysis)
    engines_r_dir = os.path.join(out_root, "Omega_Pools", str(current_round))
    run_engines_script(current_round, engines_r_dir)
    
    # 2. Load Engine Predictions
    engine_topk_file = os.path.join(engines_r_dir, "engine_topk_K20.csv")
    if not os.path.exists(engine_topk_file):
        logger.error(f"Engine output missing: {engine_topk_file}")
        sys.exit(1)
        
    engine_topk_df = pd.read_csv(engine_topk_file)
    
    # Check predictions valid
    import ast
    engine_topk_map = {}
    for _, r in engine_topk_df.iterrows():
        try:
            nums = ast.literal_eval(r['numbers']) if isinstance(r['numbers'], str) else r['numbers']
            engine_topk_map[r['engine_id']] = nums
        except:
            engine_topk_map[r['engine_id']] = []

    # 3. Update KPI (Recall Check)
    # Load Engine History (JSON)
    hist_file = os.path.join(kpi_dir, "engine_history_topk.json")
    full_history = {}
    if os.path.exists(hist_file):
        with open(hist_file, 'r') as f:
            try:
                full_history = json.load(f) # {Eng: {R_str: [nums]}}
            except json.JSONDecodeError:
                full_history = {}
            
    # Update History with current R
    for eng, nums in engine_topk_map.items():
        if eng not in full_history:
            full_history[eng] = {}
        full_history[eng][str(current_round)] = nums
        
    # Save History
    with open(hist_file, 'w') as f:
        json.dump(full_history, f)
        
    # History Format Convert for KPI func: {eng: {int(R): [nums]}}
    formatted_history = {}
    for eng, rounds in full_history.items():
        formatted_history[eng] = {int(r): n for r, n in rounds.items()}
        
    exclusions = load_exclude_rounds()
    
    # Calculate KPI
    kpi_df = update_engine_kpi(
        kpi_csv_path=os.path.join(kpi_dir, "engine_kpi.csv"),
        engine_topk_by_round=formatted_history,
        ssot_sorted_df=ssot_sorted,
        exclusions=exclusions,
        k_eval=K_EVAL
    )
    
    kpi_save_path = os.path.join(kpi_dir, "engine_kpi.csv")
    kpi_df.to_csv(kpi_save_path, index=False)
    logger.info(f"KPI Updated and saved to {kpi_save_path}")
    
    # 4. Update Omega Weights (Step D)
    engine_kpis = []
    # kpi_df columns: engine_id, status, overall, recent10, recent20, recent30, n_eval_rounds
    # Ensure status column or default
    if 'status' not in kpi_df.columns:
        kpi_df['status'] = "ACTIVE"
        
    for _, row in kpi_df.iterrows():
        engine_kpis.append(EngineKPI(
            engine_id=row['engine_id'],
            status=row['status'],
            overall=row['overall'],
            recent10=row['recent10'],
            recent20=row['recent20'],
            recent30=row['recent30'],
            n_eval_rounds=int(row['n_eval_rounds'])
        ))
        
    omega_weights = softmax_weights(engine_kpis)
    
    # Save Weights
    weight_file = os.path.join(kpi_dir, "omega_weights_current.json")
    with open(weight_file, 'w') as f:
        json.dump([asdict(w) for w in omega_weights], f, indent=2)
    logger.info(f"Omega Weights Updated: {weight_file}")
    
    # =========================================================
    # PHASE 2: Next Round (Optional) - Step E
    # =========================================================
    if args.mode == 'next':
        logger.info(f"=== Phase 2: Generating Prediction for Round {next_round} ===")
        
        # 1. Run Engines for R+1
        engines_next_dir = os.path.join(out_root, "Omega_Pools", str(next_round))
        run_engines_script(next_round, engines_next_dir)
        
        # 2. Load Predictions
        next_topk_file = os.path.join(engines_next_dir, "engine_topk_K20.csv")
        if not os.path.exists(next_topk_file):
             logger.error("Engine prediction failed for next round.")
        else:
            next_topk_df = pd.read_csv(next_topk_file)
            
            candidate_map = {}
            for _, r in next_topk_df.iterrows():
                try:
                    nums = ast.literal_eval(r['numbers']) if isinstance(r['numbers'], str) else r['numbers']
                    candidate_map[r['engine_id']] = nums
                except:
                    candidate_map[r['engine_id']] = []
                    
            # 3. Build Omega Pool
            # Use computed weights from Phase 1
            pool_numbers, pool_df = build_candidate_pool(candidate_map, omega_weights)
            
            # Save Pool
            pool_csv_path = os.path.join(engines_next_dir, "omega_pool_K22.csv")
            pool_df.to_csv(pool_csv_path, index=False)
            logger.info(f"Omega Pool for R{next_round} saved to {pool_csv_path}")
        
    else:
        logger.info("Mode is 'backfill'. Skipping R+1 prediction.")

if __name__ == "__main__":
    main()
