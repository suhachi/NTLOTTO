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
    
    # shares 계산을 위해 기준값 유지

    
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
    
    # Selection JSON 보강 (SSOT 경로 자동 삽입)
    sel_path = base_dir / "docs/reports/latest/ENGINE_SELECTION_TEMPLATE.json"
    if sel_path.exists():
        sel_data = json.loads(sel_path.read_text(encoding="utf-8"))
        sel_data["ssot_sorted_path"] = s_path
        sel_data["round"] = args.round
        sel_data["M"] = args.n
        # 쿼터 적용 (shares 이미 계산됨)
        # engine_selection 포맷 대응
        if "engine_selection" in sel_data:
            for k, q in shares.items():
                if k in sel_data["engine_selection"]:
                    sel_data["engine_selection"][k]["quota"] = q
                    sel_data["engine_selection"][k]["use"] = True
        sel_path.write_text(json.dumps(sel_data, indent=2, ensure_ascii=False), encoding="utf-8")

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
