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
from ntlotto.predict.candidate_pools import build_all_candidate_pools
# from ntlotto.predict.generate_combos import generate_predictions (더 이상 사용 안 함)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--outdir", type=str, default="docs/reports/latest")
    parser.add_argument("--selection", type=str, required=True, help="Path to ENGINE_SELECTION_*.json")
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
    sel_path = Path(args.selection)
    if not sel_path.exists():
        print(f"[FAIL] Selection file not found: {sel_path}")
        sys.exit(1)
        
    out_md = str(base_dir / f"docs/reports/latest/Prediction_Set_R{args.round}_M{args.n}.md")
    out_csv = str(base_dir / f"docs/reports/latest/NTUC_{args.round}_M{args.n}_combos.csv")
    
    try:
        from ntlotto.predict.generate_combos import generate_from_selection
        res = generate_from_selection(str(sel_path), out_md, out_csv)
        print(f"[*] 글로벌 조합 M={res['M']} 생성 통과. (Actual: {res['engine_actual']})")
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    main()
