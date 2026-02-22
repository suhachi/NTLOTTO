import argparse
import sys
import json
from pathlib import Path

from ntlotto.core.report_writer import ensure_dirs
from ntlotto.score.update_weights import update_weights

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval_json", type=str, required=True, help="Path to evaluation JSON")
    parser.add_argument("--outdir", type=str, default="docs/reports/latest")

    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    out_dir = str(base_dir / args.outdir)
    ensure_dirs(out_dir)
    
    try:
        with open(args.eval_json, "r", encoding="utf-8") as f:
            eval_res = json.load(f)
    except Exception as e:
        print(f"Load JSON err: {e}")
        sys.exit(1)
        
    try:
        update_weights(eval_res, out_dir)
    except Exception as e:
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    main()
