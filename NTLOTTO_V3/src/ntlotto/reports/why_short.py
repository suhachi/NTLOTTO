from __future__ import annotations
import pandas as pd
from ..core.stats_basic import sum6, odd_even_profile, bands_profile
from ..core.stats_hotcold import topk_freq
from ..core.util_format import fmt_f, pct

def build_why_short(w_map: dict[int, pd.DataFrame], df_o: pd.DataFrame) -> str:
    # w_map keys e.g. [5,10,15,20,25,30]
    ws = sorted(list(w_map.keys()))
    if not ws: return "No data."

    lines = [
        "# WHY-Short Report",
        "단기 윈도우 크기 변화에 따른 트렌드 비교 지표입니다.",
        "",
        "## 1. Window별 핫 트렌드 변화",
        "| Window | 평균 총합 | Top 짝홀 | Top 번호대(출현율) | Top 3 Hot Numbers |",
        "|---|---|---|---|---|"
    ]

    for w in ws:
        df = w_map[w]
        if len(df) == 0: continue
        avg_sum = sum6(df).mean()
        oe = odd_even_profile(df)
        top_oe = max(oe.items(), key=lambda x: x[1])[0] if oe else "-"
        bp = bands_profile(df)
        top_band = max(bp.items(), key=lambda x: x[1]) if bp else ("-", 0.0)
        tband_s = f"{top_band[0]}({pct(top_band[1]/6 if top_band[0]!='-' else 0.0)})"
        hot3 = topk_freq(df, 3)
        hot3_s = ",".join([str(n) for n, c in hot3])

        lines.append(f"| w={w} | {fmt_f(avg_sum)} | {top_oe} | {tband_s} | {hot3_s} |")

    lines.append("")
    lines.append("## 2. 단기 vs 장기 모멘텀 (Surging)")
    lines.append("최근 5회차에서 급부상하지만 장기적으로는 차가웠던 번호 등을 관찰합니다.")

    if 5 in w_map and 30 in w_map:
        w5 = w_map[5]
        w30 = w_map[30]
        hot5 = [n for n,c in topk_freq(w5, 5)]
        hot30 = [n for n,c in topk_freq(w30, 10)]

        surging = set(hot5) - set(hot30)
        lines.append(f"- **Surging Numbers (Hot in w=5, not in top 10 of w=30)**: {sorted(list(surging))}")
    else:
        lines.append("- (w=5, w=30 데이터가 모두 있어야 분석 가능)")

    lines.append("")
    lines.append("---")
    lines.append("**결론**: 단기 지표는 엔진의 가중치를 미세조정하는 핵심 시그널입니다.")

    return "\n".join(lines)
