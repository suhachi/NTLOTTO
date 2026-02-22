import argparse
import sys
from pathlib import Path
import json

from ntlotto.core.load_ssot import load_ssot
from ntlotto.core.validate_ssot import validate_ssot
from ntlotto.core.windows import window_map
from ntlotto.core.report_writer import ensure_dirs, write_text, write_json, history_path
from ntlotto.reports.ssot_validation_report import build_validation_report

# reports
from ntlotto.reports.why_long import build_why_long
from ntlotto.reports.why_short import build_why_short
from ntlotto.contracts.report_contract import assert_report_sections, WHY_LONG_SECTIONS, WHY_SHORT_SECTIONS
from ntlotto.reports.engine_nt4 import build_eng_nt4
from ntlotto.reports.engine_nt5 import build_eng_nt5
from ntlotto.reports.engine_omega import build_eng_omega
from ntlotto.reports.engine_nto import build_eng_nto
from ntlotto.reports.engine_vpa1 import build_eng_vpa1
from ntlotto.reports.engine_ll import build_eng_ll
from ntlotto.reports.engine_pat import build_eng_pat
from ntlotto.reports.selection_template import write_selection_template

def main():
    parser = argparse.ArgumentParser(description="NTLOTTO Reports Generator")
    parser.add_argument("--round", type=int, help="Target round to analyze up to (e.g. 1211). By default uses all data.")
    parser.add_argument("--long", type=int, default=100)
    parser.add_argument("--short", type=str, default="5,10,15,20,25,30")
    parser.add_argument("--outdir", type=str, default="docs/reports/latest")
    parser.add_argument("--histdir", type=str, default="docs/reports/history")
    
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    data_dir = base_dir / "data"
    s_path = str(data_dir / "ssot_sorted.csv")
    o_path = str(data_dir / "ssot_ordered.csv")

    try:
        df_s, df_o = load_ssot(s_path, o_path)
    except Exception as e:
        print(f"[FAIL] Data loading failed: {e}")
        sys.exit(1)

    # filter by round if needed
    if args.round is not None:
        df_s = df_s[df_s["round"] <= args.round]
        df_o = df_o[df_o["round"] <= args.round]

    if len(df_s) == 0:
        print("[FAIL] No data available.")
        sys.exit(1)

    print("[*] Validating SSOT Data...")
    try:
        val_res = validate_ssot(df_s, df_o)
        print(f"  -> OK. Rows={val_res['rows']}, Round Min={val_res['round_min']}, Max={val_res['round_max']}")
    except Exception as e:
        print(f"[FAIL] Validation Failed: {e}")
        sys.exit(1)

    out_dir = base_dir / args.outdir
    hist_dir = base_dir / args.histdir
    ensure_dirs(str(out_dir), str(hist_dir))

    def _save(name: str, content: str):
        if name.endswith(".md"):
            content = "> **안내**: 엔진 선택 시 [ENGINE_SELECTION_GUIDE_V3.md](../../contracts/ENGINE_SELECTION_GUIDE_V3.md)를 참고하세요.\n\n" + content
        p = out_dir / name
        write_text(str(p), content)
        h_p = history_path(str(p))
        write_text(h_p, content)
        print(f"  -> Wrote {name}")

    print("[*] Writing SSOT Validation Report...")
    _save("SSOT_Validation.md", build_validation_report(val_res))

    print("[*] Generating Target Round Selection Template...")
    sel_path = out_dir / "ENGINE_SELECTION_TEMPLATE.json"
    write_selection_template(str(sel_path))
    sel_hist = history_path(str(sel_path))
    write_json(sel_hist, json.loads(sel_path.read_text(encoding="utf-8")))

    print("[*] Generating Reports...")
    w_shorts = [int(x.strip()) for x in args.short.split(",")]
    wm = window_map(df_s, w_shorts)
    
    why_long_body = build_why_long(df_s, df_o, args.long)
    try:
        assert_report_sections(why_long_body, WHY_LONG_SECTIONS, "WHY_Long")
    except ValueError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    _save("WHY_Long.md", why_long_body)

    why_short_body = build_why_short(wm, df_o)
    try:
        assert_report_sections(why_short_body, WHY_SHORT_SECTIONS, "WHY_Short")
    except ValueError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    _save("WHY_Short.md", why_short_body)

    _save("Engine_NT4.md", build_eng_nt4(df_s, df_o))
    _save("Engine_NT5.md", build_eng_nt5(df_s, df_o))
    _save("Engine_Omega.md", build_eng_omega(df_s, df_o))
    _save("Engine_NTO.md", build_eng_nto(df_s, df_o))
    _save("Engine_VPA1.md", build_eng_vpa1(df_s, df_o))
    _save("Engine_LL.md", build_eng_ll(df_s, df_o))
    _save("Engine_PAT.md", build_eng_pat(df_s, df_o))

    print("[DONE] Pipeline execution completed.")

if __name__ == "__main__":
    main()
