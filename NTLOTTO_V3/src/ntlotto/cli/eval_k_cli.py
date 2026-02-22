import argparse
import sys
from pathlib import Path
import json

from ntlotto.core.load_ssot import load_ssot
from ntlotto.core.report_writer import ensure_dirs, write_json, write_text
from ntlotto.engines.nt4 import EngineNT4
from ntlotto.engines.nt5 import EngineNT5
from ntlotto.engines.nto import EngineNTO
from ntlotto.engines.omega import EngineOmega
from ntlotto.engines.vpa1 import EngineVPA1
from ntlotto.engines.ll import EngineLL
from ntlotto.score.evaluate_engines_k import evaluate_engines_k

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--outdir", type=str, default="docs/reports/latest")

    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    s_path = str(base_dir / "data" / "ssot_sorted.csv")
    o_path = str(base_dir / "data" / "ssot_ordered.csv")
    
    try:
        df_s, df_o = load_ssot(s_path, o_path)
    except Exception as e:
        print(f"Data load err: {e}")
        sys.exit(1)
        
    engines = {
        "NT4": EngineNT4(),
        "NT5": EngineNT5(),
        "NTO": EngineNTO(),
        "NT-Ω": EngineOmega(),
        "NT-VPA-1": EngineVPA1(),
        "NT-LL": EngineLL(),
    }
    
    out_dir = str(base_dir / args.outdir)
    ensure_dirs(out_dir)
    
    try:
        summary = evaluate_engines_k(engines, df_s, df_o, args.k, args.n)
        
        write_json(f"{out_dir}/Engine_Eval_K{args.k}_N{args.n}.json", summary)
        md_lines = [f"# Engine Evaluation (K={args.k}, past N={args.n})", ""]
        for eng, res in summary.items():
            md_lines.append(f"## {eng}")
            md_lines.append(f"- **Mean Recall**: {res['recall_mean']:.3f}")
            md_lines.append(f"- **Bonus Hit Rate**: {res['bonus_hit_rate']:.3f}")
            
        write_text(f"{out_dir}/Engine_Eval_K{args.k}_N{args.n}.md", "\n".join(md_lines))
        print(f"[*] Eval 완료. (Saved to {out_dir}/Engine_Eval_K{args.k}_N{args.n}.json)")
        
    except Exception as e:
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    main()
