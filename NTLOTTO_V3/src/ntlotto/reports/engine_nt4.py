from __future__ import annotations
import pandas as pd
from ..core.stats_hotcold import topk_freq, bottomk_freq

def build_eng_nt4(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: NT4 (안정성 평가)",
        "NT4는 장기 빈도 분석 기반으로, 가장 안정적으로 꾸준히 나온 번호를 선호합니다.",
        ""
    ]
    if len(df_s) == 0:
        lines.append("데이터가 부족합니다.")
        return "\n".join(lines)

    hot15 = topk_freq(df_s, 15)
    cold10 = bottomk_freq(df_s, 10)

    lines.append("## 핵심 모멘텀")
    lines.append(f"- **Top 15 장기 빈출수**: {', '.join(str(n) for n,c in hot15)}")
    lines.append(f"- **Bottom 10 소외수**: {', '.join(str(n) for n,c in cold10)}")
    lines.append("")
    lines.append("- NT4 조합은 기본적으로 위의 장기 빈출수 풀(pool)을 60% 이상 포함하도록 세팅됩니다.")

    return "\n".join(lines)
