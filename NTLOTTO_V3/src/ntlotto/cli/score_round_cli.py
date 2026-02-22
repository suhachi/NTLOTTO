import argparse
import sys
import pandas as pd
from pathlib import Path

from ntlotto.core.load_ssot import load_ssot
from ntlotto.score.score_predictions import score_predictions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True, help="Target round to score")
    parser.add_argument("--combos", type=str, required=True, help="CSV path of combinations")
    parser.add_argument("--outdir", type=str, default="docs/reports/latest")

    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    s_path = str(base_dir / "data" / "ssot_sorted.csv")
    o_path = str(base_dir / "data" / "ssot_ordered.csv")
    
    try:
        df_s, _ = load_ssot(s_path, o_path)
    except Exception as e:
        print(f"Data load err: {e}")
        sys.exit(1)
        
    try:
        combos_df = pd.read_csv(args.combos)
    except Exception as e:
        print(f"Combos load err: {e}")
        sys.exit(1)
        
    out_dir = str(base_dir / args.outdir)
    try:
        score_predictions(combos_df, df_s, args.round, out_dir)
    except Exception as e:
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    main()
