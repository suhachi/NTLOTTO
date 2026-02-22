from __future__ import annotations
import pandas as pd
from ..core.stats_recency import recency_prev1

def build_eng_omega(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: 오메가 (사각지대 커버, 이월 & 소외)",
        "오메가는 다른 엔진들이 다루지 않은 패턴(예: 극단적 소외수, 직전 이월수)을 집중 공략합니다.",
        ""
    ]
    if len(df_s) == 0:
        lines.append("데이터가 부족합니다.")
        return "\n".join(lines)

    ol = recency_prev1(df_s)
    if ol:
        avg_ol = sum(ol) / len(ol)
    else:
        avg_ol = 0.0

    lines.append("## 이월수 특성")
    lines.append(f"- **최근 이월율 평균(1회 전)**: {avg_ol:.2f}개")
    if len(df_s) >= 1:
        last_nums = [int(df_s.iloc[-1][f"n{i}"]) for i in range(1,7)]
        lines.append(f"- **직전 회차 번호 (잠재적 이월 후보)**: {last_nums}")

    lines.append("")
    lines.append("- 오메가는 이 후보들 중 1~2개를 고정하고, 나머지 자리는 NT4/NT5에서 버린 초냉각수(Cold)를 섞습니다.")
    return "\n".join(lines)
