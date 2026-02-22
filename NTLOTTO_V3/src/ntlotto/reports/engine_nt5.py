from __future__ import annotations
import pandas as pd
from ..core.stats_hotcold import topk_freq

def build_eng_nt5(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: NT5 (단기 핫 클러스터)",
        "NT5는 최근에 갑자기 터지는 번호들의 군집(Cluster)을 포착합니다.",
        ""
    ]
    w10 = df_s.tail(10) if len(df_s) >= 10 else df_s
    if len(w10) == 0:
        lines.append("데이터가 부족합니다.")
        return "\n".join(lines)

    hot5 = topk_freq(w10, 8)
    lines.append("## 단기 핫(w=10 내 Top 8) 클러스터 분석")
    nums = [n for n,c in hot5]
    lines.append(f"- **최근 10회차 다출수군**: {sorted(nums)}")

    lines.append("")
    lines.append("- NT5 조합은 최근 강세를 보이는 이 그룹을 중심축으로 조합합니다. 인접수 연번 발생 확률이 높습니다.")

    return "\n".join(lines)
