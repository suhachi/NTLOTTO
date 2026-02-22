from __future__ import annotations
import pandas as pd
from ..core.stats_basic import (
    sum6, odd_even_profile, bands_profile, run_profile, end_group_profile
)
from ..core.stats_recency import recency_overlaps, recency_prev1
from ..core.stats_hotcold import topk_freq, bottomk_freq
from ..core.stats_draw_order import gap_stats, top_transitions
from ..core.util_format import fmt_f, pct

def build_why_long(df_s: pd.DataFrame, df_o: pd.DataFrame, w1: int) -> str:
    if w1 > len(df_s): w1 = len(df_s)
    if w1 == 0: return "No data."

    s1 = df_s.tail(w1)
    o1 = df_o.tail(w1)
    start_r = int(s1["round"].min())
    end_r = int(s1["round"].max())

    # 1) 기초 지표
    sums = sum6(s1)
    avg_sum = sums.mean()
    oe_p = odd_even_profile(s1)
    top_oe = sorted(oe_p.items(), key=lambda x: -x[1])[:2]
    bp = bands_profile(s1)
    top_band = max(bp.items(), key=lambda x: x[1])

    # 2) 전이 지표
    ol_prev = recency_prev1(s1)
    no_carry_pct = sum(1 for x in ol_prev if x == 0) / max(1, len(ol_prev))
    g_stats = gap_stats(o1)
    trans = top_transitions(o1, 3)

    # 3) 형태 지표
    rp = run_profile(s1)
    ep = end_group_profile(s1)

    # 4) 누적 지표
    hot = topk_freq(s1, 10)
    cold = bottomk_freq(s1, 10)

    lines = [
        f"# WHY-Long Report",
        f"**Window**: {w1} draws (Round {start_r} ~ {end_r})",
        "",
        "## 1. 기초 지표 (Foundation)",
        f"- **평균 총합**: {fmt_f(avg_sum)}",
        f"- **자주 나오는 짝홀 비율**: {', '.join(f'{k}({v}회)' for k,v in top_oe)}",
        f"- **가장 뜨거운 번호대**: {top_band[0]} ({fmt_f(top_band[1], 2)}개/회)",
        "",
        "## 2. 전이 지표 (Flow & Gap)",
        f"- **이월수 없음(0개) 비율**: {pct(no_carry_pct)}",
        f"- **추첨순서 평균 Gap**: {fmt_f(g_stats['mean'])}",
        f"- **자주 나오는 추첨 전이**: {', '.join(f'{a}->{b}({c}회)' for (a,b),c in trans)}",
        "",
        "## 3. 형태 지표 (Shape)",
        f"- **연번 길이 프로필**: 1({rp['1']}), 2({rp['2']}), 3+({rp['3+']})",
        f"- **끝수 그룹 프로필**: 0({ep['0']}), 1({ep['1']}), 2({ep['2']}), 3+({ep['3+']})",
        "",
        "## 4. 누적 지표 (Hot/Cold)",
        f"- **Hot 10**: {', '.join(f'{n}({c})' for n,c in hot)}",
        f"- **Cold 10**: {', '.join(f'{n}({c})' for n,c in cold)}",
        "",
        "---",
        "**결론**: 장기 트렌드 요약입니다. 이 데이터는 기본 필터 한계값을 설정하는 데 사용됩니다."
    ]

    return "\n".join(lines)
