import argparse
import sys
import os
import json
import logging
import pandas as pd
from typing import List, Dict

# Adjust path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from nt_lotto.nt_core.generate import (
    build_engine_quota,
    propose_combo_candidates,
    select_portfolio,
    run_global_qa,
    ComboCandidate,
    QAReport,
    M
)
# from nt_lotto.nt_core.constants import SSOT_SORTED_CSV, SSOT_ORDERED_CSV # Removed
from nt_lotto.nt_core.constants import SSOT_SORTED, SSOT_ORDERED # Updated
from nt_lotto.nt_core.ssot_loader import load_data as load_ssot_tuple
from nt_lotto.nt_core.schema import SSOT

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("PortfolioPipeline")

def main():
    parser = argparse.ArgumentParser(description="NT Portfolio Generation Pipeline")
    parser.add_argument("--target", required=True, type=int, help="Target round")
    parser.add_argument("--train_end", required=True, type=int, help="Training end round")
    parser.add_argument("--owner_command", required=False, type=str, default="", help="Command to proceed with generation")
    parser.add_argument("--ev_exception_slots", required=False, type=int, default=0, help="Number of exception slots allowed")
    parser.add_argument("--out_root", required=True, type=str, help="Root for output artifacts")
    
    args = parser.parse_args()
    
    # 1. Paths Setup
    omega_root = os.path.join(args.out_root, "Omega_Pools", str(args.target))
    pool_csv = os.path.join(omega_root, "omega_pool_K22.csv")
    engine_topk_csv = os.path.join(omega_root, "engine_topk_K20.csv") # Assuming this exists or will be created by prev step
    
    portfolio_out_dir = os.path.join(args.out_root, "Portfolios", str(args.target))
    os.makedirs(portfolio_out_dir, exist_ok=True)
    
    # 2. Check Omega Artifacts
    if not os.path.exists(pool_csv):
        logger.error(f"Omega Pool CSV not found at {pool_csv}. Run Omega Pool step first.")
        sys.exit(1)
        
    logger.info(f"Loading Omega Pool from {pool_csv}")
    pool_df = pd.read_csv(pool_csv)
    # Ensure column 'number' exists and is sorted by rank (assuming rank is implicit row order or explicit)
    # If 'rank' column exists, sort by it.
    if 'rank' in pool_df.columns:
        pool_df = pool_df.sort_values('rank')
    
    pool_numbers = pool_df['number'].tolist()
    if len(pool_numbers) != 22:
        logger.warning(f"Omega Pool size is {len(pool_numbers)}, expected 22.")

    # 3. Check Owner Command
    if args.owner_command != "GENERATE_50":
        logger.info("Owner command != GENERATE_50. Stopping after pool verification.")
        stop_md = os.path.join(portfolio_out_dir, "STOP_NO_GENERATION.md")
        with open(stop_md, "w", encoding="utf-8") as f:
            f.write(f"# STOP: No Generation Command\n")
            f.write(f"- Target: {args.target}\n")
            f.write(f"- Received Command: {args.owner_command}\n")
            f.write(f"- Action: Artifacts loaded but Generation skipped.\n")
        sys.exit(0)

    # 4. Starting Generation
    logger.info("Starting GENERATE_50 sequence...")
    
    # Load SSOT (read-only)
    df_sorted, df_ordered = load_ssot_tuple(exclusion_mode=True)
    ssot = SSOT(sorted_df=df_sorted, ordered_df=df_ordered)
    
    # Engine TopK (Optional / Stub)
    engine_topk = {}
    if os.path.exists(engine_topk_csv):
        try:
            topk_df = pd.read_csv(engine_topk_csv)
            # Parse structure: assumption engine_id, numbers (list/str)
            # Logic here depends on format from run_omega_pool.py or engine eval
            pass
        except Exception as e:
            logger.warning(f"Failed to load engine_topk: {e}")
            
    # Per-Engine Candidate Proposal
    quota = build_engine_quota()
    candidates_by_engine = {}
    
    for engine_id in quota.keys():
        logger.info(f"Proposing candidates for {engine_id}...")
        cands = propose_combo_candidates(
            engine_id=engine_id,
            pool=pool_numbers,
            engine_topk=engine_topk,
            ssot_sorted_df=ssot.sorted_df,
            features_cache=None,
            limit=2000 # Deterministic limit
        )
        candidates_by_engine[engine_id] = cands
        logger.info(f"  > {len(cands)} candidates generated.")

    # Portfolio Selection
    qa_policy = {
        "max_overlap": 2, # Hard
        "max_freq": 8,    # Soft
        "max_jaccard": 0.30 # Soft
    }
    
    logger.info("Selecting Portfolio...")
    final_combos, report = select_portfolio(
        candidates_by_engine=candidates_by_engine,
        quota=quota,
        qa_policy=qa_policy,
        ev_exception_slots=args.ev_exception_slots
    )
    
    # 5. Global QA & Output
    if not (report.hard_pass and report.portfolio_size == 50):
        logger.error("Portfolio Selection Failed Hard Rules or Size Check.")
        logger.error(f"Size: {report.portfolio_size}, Overlap Violations: {report.overlap_violations}")
        
        fail_md = os.path.join(portfolio_out_dir, "GENERATION_FAILED.md")
        with open(fail_md, "w", encoding="utf-8") as f:
            f.write(f"# GENERATION FAILED\n")
            f.write(f"- Size: {report.portfolio_size}/50\n")
            f.write(f"- Overlap Violations: {report.overlap_violations}\n")
        sys.exit(1) # Fail fast

    # Save Success Artifacts
    logger.info("Generation Successful. Saving Artifacts.")
    
    # CSV
    rows = []
    for idx, c in enumerate(final_combos, 1):
        rows.append({
            "engine": c.engine_id,
            "combo_id": f"C{idx:02d}",
            "numbers": str(sorted(c.numbers)), # Sort consistency
            "score": round(c.score, 4),
            "meta_json": json.dumps(c.meta)
        })
    pd.DataFrame(rows).to_csv(os.path.join(portfolio_out_dir, "portfolio_50.csv"), index=False)
    
    # MD
    with open(os.path.join(portfolio_out_dir, "portfolio_50.md"), "w", encoding="utf-8") as f:
        f.write("# Portfolio 50 (Detailed)\n\n")
        curr_eng = ""
        for r in rows:
            if r["engine"] != curr_eng:
                f.write(f"## {r['engine']}\n")
                curr_eng = r["engine"]
            f.write(f"- **{r['combo_id']}**: {r['numbers']} (Score: {r['score']})\n")

    # QA Report JSON/MD
    qa_dict = {
        "target": args.target,
        "overlap_violations": report.overlap_violations,
        "freq_violations": report.freq_violations,
        "jaccard_violations": report.jaccard_violations,
        "size": report.portfolio_size,
        "hard_pass": report.hard_pass,
        "soft_pass": report.soft_pass
    }
    with open(os.path.join(portfolio_out_dir, "qa_report.json"), "w", encoding="utf-8") as f:
        json.dump(qa_dict, f, indent=2)

    with open(os.path.join(portfolio_out_dir, "qa_report.md"), "w", encoding="utf-8") as f:
        f.write("# QA Report\n\n")
        f.write(f"- **Target**: {args.target}\n")
        f.write(f"- **Hard Pass (Size=50, Overlap<=2)**: {'PASS' if report.hard_pass else 'FAIL'}\n")
        f.write(f"- **Soft Pass (Freq<=8, Jaccard<=0.3)**: {'PASS' if report.soft_pass else 'WARN'}\n")
        f.write(f"- Overlap Violations: {report.overlap_violations}\n")
        f.write(f"- Freq Violations: {report.freq_violations}\n")

    # Provenance
    with open(os.path.join(portfolio_out_dir, "provenance.md"), "w", encoding="utf-8") as f:
        f.write("# Provenance\n")
        f.write(f"- Execution Time: {pd.Timestamp.now()}\n")
        f.write(f"- Arguments: {args}\n")
        f.write(f"- Omega Pool Source: {pool_csv}\n")
    
    logger.info(f"Artifacts saved to {portfolio_out_dir}")

if __name__ == "__main__":
    main()
