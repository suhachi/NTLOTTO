import argparse
import sys
import json
from pathlib import Path

from ntlotto.core.load_ssot import load_ssot
from ntlotto.engines.nt4 import EngineNT4
from ntlotto.engines.nt5 import EngineNT5
from ntlotto.engines.nto import EngineNTO
from ntlotto.engines.omega import EngineOmega
from ntlotto.engines.vpa1 import EngineVPA1
from ntlotto.engines.ll import EngineLL
from ntlotto.engines.pat import EnginePAT
from ntlotto.predict.candidate_pools import build_candidate_pools
from ntlotto.predict.generate_combos import generate_predictions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--outdir", type=str, default="docs/reports/latest")
    parser.add_argument("--i_understand_and_allow_generation", action="store_true")

    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    s_path = str(base_dir / "data" / "ssot_sorted.csv")
    o_path = str(base_dir / "data" / "ssot_ordered.csv")
    
    try:
        df_s, df_o = load_ssot(s_path, o_path)
    except Exception as e:
        print(f"Data load err: {e}")
        sys.exit(1)
        
    df_s = df_s[df_s["round"] < args.round]
    df_o = df_o[df_o["round"] < args.round]
    
    engines = {
        "NT4": EngineNT4(),
        "NT5": EngineNT5(),
        "NTO": EngineNTO(),
        "NT-Ω": EngineOmega(),
        "NT-VPA-1": EngineVPA1(),
        "NT-LL": EngineLL(),
        "NT-PAT": EnginePAT()
    }
    
    pools = build_candidate_pools(engines, df_s, df_o)
    
    # 쿼터 분배
    shares = {
        "NT4": int(args.n * 0.2),
        "NT5": int(args.n * 0.2),
        "NTO": int(args.n * 0.3),
        "NT-Ω": int(args.n * 0.1),
        "NT-VPA-1": int(args.n * 0.1),
        "NT-LL": int(args.n * 0.1),
    }
    # 남는/부족분은 NTO에 조정
    diff = args.n - sum(shares.values())
    shares["NTO"] += diff
    
    out_dir = str(base_dir / args.outdir)
    try:
        generate_predictions(args.round, args.n, pools, shares, out_dir, args.i_understand_and_allow_generation)
    except Exception as e:
        print(f"[FAIL] {e}")
        
if __name__ == "__main__":
    main()
