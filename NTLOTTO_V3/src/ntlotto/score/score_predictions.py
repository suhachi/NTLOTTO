from __future__ import annotations
import pandas as pd
import csv
from ..core.report_writer import ensure_dirs, write_text

def get_rank(match_count: int, has_bonus: bool) -> str:
    if match_count == 6: return "1등"
    if match_count == 5 and has_bonus: return "2등"
    if match_count == 5: return "3등"
    if match_count == 4: return "4등"
    if match_count == 3: return "5등"
    return "낙첨"

def score_predictions(combos_df: pd.DataFrame, df_s: pd.DataFrame, target_round: int, out_dir: str):
    """
    당첨 번호와 비교하여 조합 파일 채점 진행
    """
    row = df_s[df_s["round"] == target_round]
    if len(row) == 0:
        raise ValueError(f"Round {target_round} not found in SSOT")
        
    win_nums = set(int(row.iloc[0][f"n{i}"]) for i in range(1, 7))
    v_bonus = int(row.iloc[0]["bonus"])
    
    results = []
    
    for _, c_row in combos_df.iterrows():
        c_nums = [int(c_row[f"n{i}"]) for i in range(1, 7)]
        ov = win_nums.intersection(set(c_nums))
        match_c = len(ov)
        has_b = (v_bonus in c_nums)
        rank = get_rank(match_c, has_b)
        
        results.append({
            "combo": sorted(c_nums),
            "matched_nums": sorted(list(ov)),
            "match_count": match_c,
            "has_bonus": has_b,
            "rank": rank
        })
        
    # Write CSV
    ensure_dirs(out_dir)
    csv_path = f"{out_dir}/Score_R{target_round}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["예측번호", "일치번호", "일치갯수", "등수"])
        for r in results:
            w.writerow([r["combo"], r["matched_nums"], r["match_count"], r["rank"]])
            
    # Write MD
    md_lines = [
        f"# Score Report Round {target_round}",
        f"**당첨 번호**: {sorted(list(win_nums))} + 보너스 {v_bonus}",
        "",
        "## 채점 결과",
        "| 예측번호 | 일치번호 | 일치갯수 | 보너스 | 등수 |",
        "|---|---|---|---|---|"
    ]
    for r in results:
        md_lines.append(f"| {r['combo']} | {r['matched_nums']} | {r['match_count']} | {'O' if r['has_bonus'] else 'X'} | {r['rank']} |")
        
    write_text(f"{out_dir}/Score_R{target_round}.md", "\n".join(md_lines))
    print(f"[*] 채점 완료. (Saved to {out_dir}/Score_R{target_round}.md)")
