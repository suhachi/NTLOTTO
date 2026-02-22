import argparse
import sys
import os

from ntlotto.core.load_ssot import load_ssot
from ntlotto.core.validate_ssot import validate_ssot
from ntlotto.reports.why_long import generate_why_long
from ntlotto.reports.why_short import generate_why_short

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NTLOTTO v3: Generate SSOT Validation and WHY Reports.")
    parser.add_argument("--round", type=int, required=True, help="Target round number (for report filename mainly)")
    parser.add_argument("--long", type=int, default=100, help="Window size for WHY-Long report")
    parser.add_argument("--short", type=str, default="5,10,15,20,25,30", help="Comma separated window sizes for WHY-Short report")
    return parser

def main():
    parser = init_argparse()
    args = parser.parse_args()
    
    print("=========================================")
    print(f" [NTLOTTO v3] Sprint A Report Generator")
    print("=========================================")
    
    # 1. Load Data
    try:
        df_sorted, df_ordered = load_ssot()
        print(f"[INFO] Loaded SSOT Data successfully. (Total rows: {len(df_sorted)})")
    except Exception as e:
        print(f"[ERROR] Failed to load SSOT: {e}")
        sys.exit(1)
        
    actual_max_round = df_sorted['round'].max()
    if args.round != actual_max_round:
        print(f"[WARN] Target round passed ({args.round}) does not match maximum round in SSOT ({actual_max_round}). Reports will be named R{args.round} but calculated based on SSOT data up to {actual_max_round}.")
        
    # Override for calculations to make sure we use what we strictly have
    target_calc_round = actual_max_round
        
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    reports_dir = os.path.join(base_dir, "docs", "reports")
    latest_dir = os.path.join(reports_dir, "latest")
    os.makedirs(latest_dir, exist_ok=True)
    os.makedirs(os.path.join(reports_dir, "history"), exist_ok=True)
    
    # 2. Validate SSOT
    try:
        validate_ssot(df_sorted, df_ordered)
        val_content = f"# SSOT Validation Report\n\n- **Target Round**: {args.round}\n- **Max Round Found**: {actual_max_round}\n- **Status**: PASSED\n"
    except ValueError as e:
        print(f"[FATAL] Validation Error: {e}")
        val_content = f"# SSOT Validation Report\n\n- **Target Round**: {args.round}\n- **Max Round Found**: {actual_max_round}\n- **Status**: FAILED\n- **Error**: {e}\n"
        with open(os.path.join(latest_dir, "SSOT_Validation.md"), "w", encoding="utf-8") as f:
            f.write(val_content)
        sys.exit(1)
        
    with open(os.path.join(latest_dir, "SSOT_Validation.md"), "w", encoding="utf-8") as f:
        f.write(val_content)
        
    # 3. Generating Reports
    # Parse short windows
    try:
        short_windows = [int(x.strip()) for x in args.short.split(",")]
    except ValueError:
        print("[ERROR] Invalid format for --short argument. Use comma-separated integers.")
        sys.exit(1)
        
    print("\n>> Generating WHY-Long Report...")
    generate_why_long(base_dir, df_sorted, df_ordered, target_calc_round, args.long)
    
    print(">> Generating WHY-Short Report...")
    generate_why_short(base_dir, df_sorted, target_calc_round, short_windows)
    
    print("\n[SUCCESS] Pipeline executed completely.")

if __name__ == "__main__":
    main()
